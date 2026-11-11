"""Roda antes de qualquer módulo de teste: nenhum teste usa o banco REAL (data/perfect_shock.db).
database.DB_PATH é lido na importação; por isso o PSD_DB é apontado aqui, para um banco temporário, antes de qualquer import do app.
Módulos que precisam de um banco próprio (test_integration) sobrescrevem o PSD_DB antes de importar o app."""
import os, tempfile

_REAL = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "perfect_shock.db"))
if not os.environ.get("PSD_DB") or os.path.abspath(os.environ["PSD_DB"]).lower() == _REAL.lower():
    os.environ["PSD_DB"] = os.path.join(tempfile.mkdtemp(prefix="psd_test_"), "app.db")
os.environ.setdefault("PSD_SCHEDULER", "off")
