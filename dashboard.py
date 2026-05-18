import uvicorn

if __name__ == '__main__':
    uvicorn.run('afra_market_data.dashboard:app', host='127.0.0.1', port=8090, reload=False)
