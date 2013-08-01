from mock import patch, Mock
from moto.server import main


@patch('sys.stderr', Mock())    # Supressing argparse complaints
def test_wrong_arguments():
    (main.when.called_with(["name", "test1", "test2", "test3"])
     .should.throw(SystemExit))


@patch('moto.server.app.run')
def test_right_arguments(app_run):
    main(["s3"])
    app_run.assert_called_once_with(host='0.0.0.0', port=5000)


@patch('moto.server.app.run')
def test_port_argument(app_run):
    main(["s3", "--port", "8080"])
    app_run.assert_called_once_with(host='0.0.0.0', port=8080)
