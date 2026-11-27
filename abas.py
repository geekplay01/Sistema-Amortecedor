"""Update 8 · fechar o sistema quando a última aba do app fecha.

Cada página aberta avisa que chegou (`ping`, também a cada 30 s) e, ao sair, que saiu (`saiu`, por navigator.sendBeacon no pagehide).
Trocar de tela não fecha: a tela nova avisa que chegou antes de vencer a folga (`GRACA`, 15 s).
Regras (decididas com o usuário):
  • Fecha só depois de uma saída de verdade (aviso de saída) e sem nenhuma aba viva durante a folga. Sem aviso de saída, nada fecha:
    travar a tela, suspender o PC ou o navegador travar deixam o app aberto.
  • Aba do próprio PC fica viva até avisar que saiu (não vence por tempo: com o PC suspenso ela não manda sinal).
  • Aba de outro aparelho (celular) conta como viva enquanto manda sinal (até `CELULAR` s sem sinal), porque o celular nem sempre avisa que saiu.
  • Não fecha no meio de trabalho (sincronização, importação, backup ou outra requisição em curso): espera terminar.
Só liga quando o app é aberto pelo atalho (app.py, pythonw); testes e cópias de conferência não fecham sozinhos.
"""
import threading, time

GRACA = 15          # s depois do último aviso de saída
CELULAR = 180       # s sem sinal para uma aba de outro aparelho deixar de contar

_lock = threading.Lock()
_abas = {}          # id → {"t": último sinal, "local": bool}
_saida = [None]     # hora do último aviso de saída


def ping(aba, local, agora=None):
    if not aba: return
    with _lock: _abas[str(aba)[:64]] = {"t": time.time() if agora is None else agora, "local": bool(local)}


def saiu(aba, agora=None):
    with _lock:
        _abas.pop(str(aba or "")[:64], None); _saida[0] = time.time() if agora is None else agora


def vivas(agora=None):
    agora = time.time() if agora is None else agora
    with _lock: return [k for k, a in _abas.items() if a["local"] or agora - a["t"] <= CELULAR]


def deve_fechar(ocupado=False, agora=None):
    """True quando houve aviso de saída há mais de GRACA s, não há aba viva e nada está em andamento."""
    agora = time.time() if agora is None else agora
    s = _saida[0]
    return s is not None and agora - s >= GRACA and not vivas(agora) and not ocupado


def zerar():
    with _lock: _abas.clear(); _saida[0] = None


def iniciar(ocupado, fechar, passo=3):
    """Vigia em segundo plano: a cada `passo` s confere `deve_fechar(ocupado())` e chama `fechar()` uma vez."""
    def loop():
        while True:
            time.sleep(passo)
            try:
                if deve_fechar(ocupado()): fechar(); return
            except Exception:
                pass
    t = threading.Thread(target=loop, name="psd-abas", daemon=True); t.start(); return t
