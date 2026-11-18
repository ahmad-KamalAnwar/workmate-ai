from app.auth.security import hash_password, hash_token, new_session_token, verify_password


def test_password_round_trip() -> None:
    hashed = hash_password("a long enough password")
    assert hashed.startswith("$argon2id$")
    assert verify_password(hashed, "a long enough password")
    assert not verify_password(hashed, "a different password")


def test_missing_hash_never_verifies() -> None:
    assert not verify_password(None, "anything")


def test_corrupt_hash_does_not_raise() -> None:
    assert not verify_password("not-a-hash", "anything")


def test_session_tokens_are_unique_and_hashed_deterministically() -> None:
    a, b = new_session_token(), new_session_token()
    assert a != b
    assert len(a) >= 43  # 32 random bytes, url-safe base64
    assert hash_token(a) == hash_token(a)
    assert hash_token(a) != a
    assert len(hash_token(a)) == 64
