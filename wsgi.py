from application import app

if __name__ == '__main__':
    flask_options = dict(
        host='0.0.0.0',
        debug=True,
        port=5001,
        threaded=True,
    )

    app.run(**flask_options)
