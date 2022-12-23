import fastapi

app = fastapi.FastAPI()


class Response(fastapi.Response):
    pass


@app.post("/post")
async def post(req: fastapi.Request, rsp: fastapi.Response):
    print(await req.body())
    print(req.cookies)
    rsp.set_cookie("age", "3123")
    rsp.set_cookie("name", "tom")
    return {"code": 100}


@app.get("/post")
async def post_get(req: fastapi.Request, rsp: fastapi.Response):
    print(await req.body())
    print(req.cookies)
    rsp.set_cookie("age", "3123")
    rsp.set_cookie("name", "tom")
    return {"code": 100}
