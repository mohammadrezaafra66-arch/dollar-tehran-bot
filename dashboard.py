import uvicorn

if __name__ == "__main__":
    uvicorn.run("dollar_bot.web:app", host="127.0.0.1", port=8090, reload=False)
