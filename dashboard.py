import os

import uvicorn


if __name__ == '__main__':
    host = os.getenv('AFRA_DASHBOARD_HOST', '127.0.0.1')
    port = int(os.getenv('AFRA_DASHBOARD_PORT', '8090'))
    uvicorn.run('afra_market_data.dashboard:app', host=host, port=port, reload=False)
