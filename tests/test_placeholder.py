def test_project_imports():
    import django  # noqa: F401

    assert django.VERSION >= (5, 0)
