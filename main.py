"""
Entrypoint principal del proyecto de tesis: Optimizador de Horarios UNMSM.

La plataforma opera oficialmente a través de la aplicación web interactiva en Streamlit (app.py).
Este archivo actúa como lanzador directo hacia la interfaz web oficial.
"""
import sys
import subprocess


def main():
    print("=" * 70)
    print("  🎓 OPTIMIZADOR DE HORARIOS UNMSM — PLATAFORMA WEB OFICIAL")
    print("  Escuela Profesional de Ingeniería de Sistemas · FISI UNMSM")
    print("=" * 70)
    print("Iniciando la aplicación web en http://localhost:8501 ...\n")
    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py"])
    except KeyboardInterrupt:
        print("\n👋 Servidor Streamlit finalizado.")


if __name__ == "__main__":
    main()
