from util.http import init_session, close_sessoin


class Context:
    async def __aenter__(self, *args):
        await init_session()
        # restore_cookie()

    async def __aexit__(self, *args):
        await close_sessoin()
