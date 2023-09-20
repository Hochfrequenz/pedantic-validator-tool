from pvtool import return_foo


class TestPvTool:
    def test_return_foo(self):
        assert return_foo() == "foo"
