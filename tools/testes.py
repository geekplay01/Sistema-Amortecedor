"""Roda a suíte inteira, um módulo por processo (o teste de integração exige processo próprio), e confere no fim que o banco REAL não mudou.
Uso (na pasta do projeto):   .venv\\Scripts\\python.exe tools\\testes.py            → todos
                              .venv\\Scripts\\python.exe tools\\testes.py pipeline   → só os módulos cujo nome contém «pipeline»
Saída 0 = tudo verde."""
import os, sys, glob, hashlib, subprocess, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REAL = os.path.join(ROOT, "data", "perfect_shock.db")

def digest(p):
    if not os.path.exists(p): return None
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""): h.update(b)
    return h.hexdigest()

def main(filtro=""):
    mods = sorted(os.path.splitext(os.path.basename(p))[0] for p in glob.glob(os.path.join(ROOT, "tests", "test_*.py")))
    mods = [m for m in mods if filtro in m]
    env = dict(os.environ, PYTHONIOENCODING="utf-8", PSD_SCHEDULER="off")
    env.pop("PSD_DB", None)                       # cada teste escolhe o próprio banco temporário
    antes, falhas, t0 = digest(REAL), [], time.time()
    for m in mods:
        t = time.time(); r = subprocess.run([sys.executable, "-m", "unittest", f"tests.{m}"], cwd=ROOT, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace")
        resumo = next((l for l in reversed(r.stderr.splitlines()) if l.startswith(("OK", "FAILED"))), "?")
        print(f"{'ok ' if r.returncode == 0 else 'ERRO'}  {m:20} {time.time() - t:5.1f}s  {resumo}")
        if r.returncode: falhas.append(m); print("\n".join("      " + l for l in r.stderr.splitlines() if l.startswith(("FAIL:", "ERROR:", "AssertionError", "  File"))))
    intacto = digest(REAL) == antes
    print(f"\n{len(mods) - len(falhas)}/{len(mods)} módulos verdes em {time.time() - t0:.0f}s · banco real {'intacto' if intacto else 'ALTERADO PELOS TESTES!'}")
    return 0 if not falhas and intacto else 1

if __name__ == "__main__": sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else ""))
