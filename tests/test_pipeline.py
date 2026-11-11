"""Teste offline do data_pipeline: um SQLite faz o papel do SQL Server (nenhuma rede/senha necessária).
Rodar:  python -m unittest tests.test_pipeline -v   (na pasta do projeto)"""
import os, sys, sqlite3, tempfile, unittest, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import data_pipeline as dp

COLS = ['CÓDIGO', 'SUGESTÃO', 'STATUS', 'SUB STATUS VALIDAÇÃO', 'SUB STATUS PROJETO / INVOICE', 'CURTIU', 'NÃO CURTIU', 'FORNECEDOR', 'MARCA', 'AMOSTRA ENVIADA', 'PEDIDO CONFIRMADO', 'OEM', 'IPI']
ROWS = [
    ('AMD0170', 'des ', 'em cotacao', None, 'PENDENTE COMPRAS', 1, 0, 'zs', 'perfect', None, None, '1BP31901AB / AMD08321', '2.6'),
    ('AMD0170', 'DES', 'EM COTAÇÃO', 'VALIDAÇÃO REPROVADA QUALIDADE', None, 1, 0, 'ZS', 'PERFECT', None, None, None, None),   # 2ª aplicação do mesmo código
    ('1BP38560AA', 'Desenv.', 'PEDIDO CONFIRMADO', None, None, 0, 0, 'E-WIN', 'BPROAUTO', '2026-03-10 00:00:00', '2026-02-01', None, None),
    ('AMD0222', 'R-D', 'PENDENTE CONFIRMACAO', None, None, None, 1, 'ZS', 'PERFECT', None, None, None, None),
    ('amd0300', ' rd', 'ITEM RECEBIDO ', None, None, None, None, 'XGM', 'PERFECT', None, None, None, None),
    ('AMD0400', 'Redesenvolvimento', 'EM COTAÇÃO', None, None, None, None, 'ZS', 'PERFECT', None, None, None, None),
    ('AMD0500', 'xyz', 'STATUS NOVO QUALQUER', None, None, None, None, None, None, None, None, None, None),
    (None, 'DES', 'EM COTAÇÃO', None, None, None, None, None, None, None, None, None, None),                                    # sem código: descartada
] + [(f'AMD9{i:03d}', 'DES', 'EM COTAÇÃO', None, None, None, None, 'ZS', 'PERFECT', None, None, None, None) for i in range(30)]


def make_server(path, rows=ROWS, table='DESENVOLVIMENTO_PRODUTOS'):
    c = sqlite3.connect(path); c.execute(f'DROP TABLE IF EXISTS "{table}"')
    c.execute(f'CREATE TABLE "{table}" (' + ','.join(f'"{x}"' for x in COLS) + ')')
    c.executemany(f'INSERT INTO "{table}" VALUES ({",".join("?" * len(COLS))})', rows); c.commit(); c.close()


class Pipeline(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(); self.server = os.path.join(self.tmp, 'server.db'); make_server(self.server)
        self.store = dp.Store(os.path.join(self.tmp, 'cache.db')); self.cfg = dp.Config(user='pwbi.desenvolvimento', password='s3cr3t@}x')
        self.factory = lambda cfg: sqlite3.connect(self.server)

    def sync(self): return dp.sync(self.cfg, self.store, self.factory)
    def ev(self, **kw):
        c = self.store.conn(); w = ' AND '.join(f'{k}=?' for k in kw)
        r = [dict(x) for x in c.execute(f'SELECT * FROM dev_status_events WHERE {w} ORDER BY id', list(kw.values()))]; c.close(); return r

    # ---- normalização ----
    def test_kind_labels(self):
        for raw, exp in [('DES', dp.KIND_DES), ('des ', dp.KIND_DES), ('Desenv.', dp.KIND_DES), ('DESENVOLVIMENTO', dp.KIND_DES), ('R-D', dp.KIND_RD), ('r-d', dp.KIND_RD), (' rd', dp.KIND_RD),
                         ('R/D', dp.KIND_RD), ('Redesenvolvimento', dp.KIND_RD), ('REDESENVOLVIMENTO ', dp.KIND_RD), ('xyz', None), (None, None), ('', None)]:
            self.assertEqual(dp.normalize_kind(raw), exp, raw)

    def test_status_dates_flags(self):
        self.assertEqual(dp.normalize_status('em cotacao'), 'EM COTAÇÃO'); self.assertEqual(dp.normalize_status('PENDENTE CONFIRMACAO'), 'PENDENTE CONFIRMAÇÃO')
        self.assertEqual(dp.normalize_status('pendente cod perfect'), 'PENDENTE COD. PERFECT'); self.assertEqual(dp.normalize_status(' item   recebido '), 'ITEM RECEBIDO')
        self.assertEqual(dp.to_date('2026-03-10 00:00:00'), '2026-03-10'); self.assertEqual(dp.to_date('10/03/2026'), '2026-03-10'); self.assertIsNone(dp.to_date('NULL'))
        self.assertEqual((dp.to_int('SIM'), dp.to_int('não'), dp.to_int('3.0'), dp.to_int(None)), (1, 0, 3, None))

    def test_normalize_frame(self):
        conn = sqlite3.connect(self.server); f = dp.locate(conn, ['DESENVOLVIMENTO_PRODUTOS'], self.cfg); res = dp.normalize_dev(dp.extract_raw(conn, f['DESENVOLVIMENTO_PRODUTOS']))
        self.assertEqual(set(res.rows['kind'].dropna()), {dp.KIND_DES, dp.KIND_RD}); self.assertEqual(res.warnings['linha_sem_codigo'], 1); self.assertEqual(res.warnings['tipo_desconhecido'], 1)
        self.assertIn('status_novo:STATUS NOVO QUALQUER', res.warnings)
        r = res.rows[res.rows.code == 'AMD0300'].iloc[0]; self.assertEqual((r.kind, r.status, r.supplier), (dp.KIND_RD, 'ITEM RECEBIDO', 'XGM'))       # 'amd0300' -> AMD0300
        e = json.loads(res.rows[(res.rows.code == 'AMD0170')].iloc[0].extra); self.assertEqual(e['OEM'], '1BP31901AB / AMD08321'); self.assertEqual(e['IPI'], '2.6')   # nada se perde
        it = res.items[(res.items.code == 'AMD0170') & (res.items.kind == dp.KIND_DES)].iloc[0]; self.assertEqual((it.n_rows, it.status, it.curtiu), (2, 'EM COTAÇÃO', 1))
        self.assertIn('PENDENTE COMPRAS', it.substatus); self.assertIn('VALIDAÇÃO REPROVADA QUALIDADE', it.substatus)
        self.assertEqual(res.rows[res.rows.code == '1BP38560AA'].iloc[0].sample_sent, '2026-03-10')

    # ---- snapshot / transições ----
    def test_baseline_then_transitions(self):
        a = self.sync(); self.assertTrue(a['ok']); self.assertTrue(a['baseline']); self.assertEqual(a['events'], 0)       # marco zero: sem eventos
        self.assertEqual(self.store.last_sync()['runs'], 1)
        rows = list(ROWS); rows[2] = ('1BP38560AA', 'DES', 'ITEM RECEBIDO', None, None, 0, 0, 'E-WIN', 'BPROAUTO', '2026-03-10', '2026-02-01', None, None)     # DES: confirmado -> recebido
        rows[3] = ('AMD0222', 'R-D', 'ITEM RECEBIDO', None, None, None, 1, 'ZS', 'PERFECT', None, None, None, None)                                             # R-D: pendente confirmação -> recebido
        rows[5] = ('AMD0400', 'Redesenvolvimento', 'PEDIDO CONFIRMADO', None, None, None, None, 'ZS', 'PERFECT', None, None, None, None)
        rows = [r for r in rows if r[0] != 'AMD0500'] + [('AMD7777', 'DES', 'PEDIDO CONFIRMADO', None, None, None, None, 'ZS', 'PERFECT', None, None, None, None)]  # um some, um novo
        make_server(self.server, rows); b = self.sync(); self.assertTrue(b['ok']); self.assertFalse(b['baseline'])
        self.assertEqual([(e['from_value'], e['to_value']) for e in self.ev(code='AMD0222', field='status')], [('PENDENTE CONFIRMAÇÃO', 'ITEM RECEBIDO')])
        self.assertEqual(self.ev(code='AMD0222', field='status')[0]['kind'], dp.KIND_RD)
        self.assertEqual([(e['from_value'], e['to_value']) for e in self.ev(code='1BP38560AA', field='status')], [('PEDIDO CONFIRMADO', 'ITEM RECEBIDO')])
        self.assertEqual(self.ev(code='AMD7777')[0]['origin'], 'novo_item'); self.assertEqual(self.ev(code='AMD0500', field='presenca')[0]['to_value'], 'AUSENTE')
        self.assertEqual(self.ev(code='AMD0400', field='status')[0]['to_value'], 'PEDIDO CONFIRMADO')
        self.assertEqual(b['new_items'], 1); self.assertEqual(b['removed_items'], 1)
        c = self.sync(); self.assertEqual(c['events'], 0)                                                             # sem mudança: idempotente
        self.assertEqual(self.store.last_sync()['runs'], 3)

    def test_backfill_is_opt_in(self):
        self.assertEqual(self.sync()['events'], 0)
        os.remove(os.path.join(self.tmp, 'cache.db')); st = dp.Store(os.path.join(self.tmp, 'cache.db')); os.environ['DEV_SYNC_BACKFILL_DATES'] = '1'
        try:
            r = dp.sync(dp.Config(user='u', password='p'), st, self.factory); self.assertTrue(r['baseline']); self.assertGreaterEqual(r['events'], 1)
            c = st.conn(); ev = c.execute("SELECT * FROM dev_status_events WHERE origin='backfill_coluna'").fetchall(); c.close(); self.assertEqual(ev[0]['at'][:10], '2026-02-01')
        finally: del os.environ['DEV_SYNC_BACKFILL_DATES']

    # ---- travas e erros ----
    def test_suspicious_load_is_rejected(self):
        self.assertTrue(self.sync()['ok']); make_server(self.server, ROWS[:2]); r = self.sync()
        self.assertFalse(r['ok']); self.assertIn('Carga suspeita', r['error'])
        c = self.store.conn(); self.assertGreater(c.execute('SELECT COUNT(*) FROM dev_item_state WHERE present=1').fetchone()[0], 30); c.close()          # nada foi marcado como ausente
        self.assertEqual(self.store.last_sync()['last_status'], 'erro')

    def test_connection_error_keeps_data_and_masks_password(self):
        self.assertTrue(self.sync()['ok'])
        def boom(cfg): raise RuntimeError('Login failed for user pwbi.desenvolvimento PWD=s3cr3t@}x senha s3cr3t@}x')
        r = dp.sync(self.cfg, self.store, boom); self.assertFalse(r['ok']); self.assertNotIn('s3cr3t', r['error']); self.assertIn('****', r['error'])
        s = self.store.last_sync(); self.assertEqual(s['last_status'], 'erro'); self.assertIsNotNone(s['last_ok_at']); self.assertNotIn('s3cr3t', s['last_error'])
        c = self.store.conn(); self.assertGreater(c.execute('SELECT COUNT(*) FROM dev_rows').fetchone()[0], 30); c.close()

    def test_trava_entre_processos(self):
        """Tarefa agendada e app aberto ao mesmo tempo: a 2ª sincronização desiste; trava velha (processo morto) é ignorada; a trava some no fim."""
        lock = dp.lock_path(self.store); open(lock, 'w').write('outro processo')
        r = self.sync(); self.assertFalse(r['ok']); self.assertIn('andamento', r['error']); self.assertTrue(os.path.exists(lock))
        old = __import__('time').time() - dp.LOCK_STALE_S - 5; os.utime(lock, (old, old))
        self.assertTrue(self.sync()['ok']); self.assertFalse(os.path.exists(lock))
        self.assertTrue(self.sync()['ok']); self.assertFalse(os.path.exists(lock))

    def test_diaria_nao_repete_no_mesmo_dia(self):
        import datetime
        manha = datetime.datetime.combine(datetime.date.today(), datetime.time(6, 30))
        self.assertTrue(dp.daily(self.cfg, self.store, self.factory, now_=manha)['ok'])                      # 1ª do dia: sincroniza
        r = dp.daily(self.cfg, self.store, self.factory, now_=manha); self.assertTrue(r['pulada']); self.assertEqual(self.store.last_sync()['runs'], 1)   # já rodou hoje: não repete
        r = dp.daily(self.cfg, self.store, self.factory, now_=manha + datetime.timedelta(days=1)); self.assertFalse(r.get('pulada')); self.assertEqual(self.store.last_sync()['runs'], 2)

    def test_missing_object_message(self):
        os.remove(self.server); make_server(self.server, table='OUTRA'); r = self.sync()
        self.assertFalse(r['ok']); self.assertIn('DESENVOLVIMENTO_PRODUTOS', r['error']); self.assertIn('probe', r['error'])

    def test_read_only_guard(self):
        for bad in ['DELETE FROM x', 'SELECT 1; DROP TABLE a', 'UPDATE x SET a=1', 'EXEC sp_who', 'SELECT * INTO novo FROM x', 'INSERT INTO x VALUES (1)', 'WITH a AS (SELECT 1) DELETE FROM x']:
            with self.assertRaises(PermissionError, msg=bad): dp.assert_select(bad)
        for ok in ['SELECT 1', "SELECT * FROM [EST DISP] WHERE a='DELETE; DROP'", 'WITH a AS (SELECT 1) SELECT * FROM a', 'SELECT TOP (5) * FROM [dbo].[X];']: dp.assert_select(ok)

    def test_locate_ignores_case_space_underscore(self):
        c = sqlite3.connect(self.server); c.execute('CREATE TABLE "EST DISP" (a)'); c.execute('CREATE VIEW pedidos_compra_detalhado AS SELECT 1 a'); c.commit()
        f = dp.locate(c, ['EST_DISP', 'PEDIDOS_COMPRA_DETALHADO', 'NAO_EXISTE'], self.cfg); self.assertEqual(set(f), {'EST_DISP', 'PEDIDOS_COMPRA_DETALHADO'}); self.assertEqual(f['PEDIDOS_COMPRA_DETALHADO']['type'], 'VIEW')
        self.assertEqual(dp.qi('EST DISP'), '[EST DISP]'); self.assertEqual(dp.qi('a]b'), '[a]]b]')

    def test_probe_reports_columns(self):
        rep = dp.probe(self.cfg, lambda cfg: sqlite3.connect(self.server), names=['DESENVOLVIMENTO_PRODUTOS', 'EST DISP'])
        self.assertEqual(rep['missing'], ['EST DISP']); info = rep['found']['DESENVOLVIMENTO_PRODUTOS']; self.assertEqual(info['linhas'], len(ROWS))
        self.assertEqual(info['reconhecimento']['mapeadas']['code'], 'CÓDIGO'); self.assertIn('OEM', info['reconhecimento']['vao_para_extra'])

    def test_column_override(self):
        raw = __import__('pandas').DataFrame({'ITEM_X': ['A1'], 'TP': ['des'], 'SIT': ['em cotacao']})
        self.assertRaises(ValueError, dp.normalize_dev, raw)
        res = dp.normalize_dev(raw, {'code': 'ITEM_X', 'kind': 'TP', 'status': 'SIT'}); self.assertEqual(res.rows.iloc[0].kind, dp.KIND_DES)


if __name__ == '__main__':
    unittest.main(verbosity=2)
