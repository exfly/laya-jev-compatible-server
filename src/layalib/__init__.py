def main() -> None:
    import logging
    import os
    import sys

    from layalib.server import make_server

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    log = logging.getLogger("layalib")

    host = os.environ.get("LAYA_HOST", "127.0.0.1")
    port = int(os.environ.get("LAYA_PORT", "8000"))
    model_dir = os.environ.get("LAYA_ML_DIR", "models/laya-multilingual")
    device = os.environ.get("LAYA_DEVICE", "cpu")

    weights = os.path.join(model_dir, "model.safetensors")
    if not os.path.isfile(weights):
        log.error("no weights at %s", weights)
        sys.exit(2)

    # ponytail: cwd 即仓库根，跟 poc 一样
    sys.path.insert(0, "laya")
    import laya

    agent = laya.load(model_dir, device=device)
    httpd = make_server(agent, host=host, port=port)
    log.info("listen %s:%s", host, httpd.server_address[1])
    httpd.serve_forever()
