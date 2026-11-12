from app.security import create_token, decode_token, hash_password, verify_password


def test_password_hash_and_verify():
    stored = hash_password("mypassword")
    assert stored != "mypassword"
    assert verify_password("mypassword", stored)
    assert not verify_password("wrongpass", stored)


def test_same_password_gives_different_hashes():
    assert hash_password("abc12345") != hash_password("abc12345")


def test_token_roundtrip():
    assert decode_token(create_token(42)) == 42


def test_tampered_token_rejected():
    token = create_token(1)
    assert decode_token(token + "x") is None
    assert decode_token("garbage") is None
