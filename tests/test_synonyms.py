import sys
import pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1] / 'src'))

from taxonomy.synonyms import build_queries

def test_en_verb_expansion():
    q = build_queries("drill screws")
    top = q[0].split()
    assert any(t.startswith("drill") for t in top)
    assert any(t in top for t in ["screw", "bolt"])

def test_nl_verb_expansion():
    q = build_queries("schroeven en boren")
    top = q[0].split()
    assert any(t in top for t in ["accuboormachine", "boor", "kolomboor"])
    assert any(t in top for t in ["schroef", "bout", "bevestiger"])


def test_en_additional_verbs():
    q = build_queries("saw and paint")
    top = q[0].split()
    assert any(t in top for t in ["handsaw", "jigsaw"])
    assert any(t in top for t in ["brush", "roller"])


def test_nl_additional_verbs():
    q = build_queries("zagen en schuren")
    top = q[0].split()
    assert any(t in top for t in ["handzaag", "decoupeerzaag"])
    assert any(t in top for t in ["schuurmachine", "schuurpapier"])
