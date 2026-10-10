from datetime import date
from publisher.core import detect_topic, local_publish_at, make_copy, natural_index


def test_numbering():
    assert natural_index("corte_fino_01_vertical.mp4") == 1
    assert natural_index("VIDEO - 05.mp4") == 5


def test_bets_copy():
    pack = make_copy("A casa sempre ganha. O problema é quando a pessoa entra no vício de aposta e cassino. Até onde vai a responsabilidade de quem divulga isso?")
    assert pack.topic == "apostas"
    assert len(pack.youtube_title) <= 100
    assert "#CorteFino" in pack.tiktok_caption


def test_politics():
    assert detect_topic("O presidente falou do governo e o congresso respondeu.") == "politica"


def test_timezone():
    assert "13:00:00" in local_publish_at(date(2026, 10, 10), 10)
