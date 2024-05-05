import pytest
from services.base import ServerUnavailable
from services.sms_activate import SMSActivateService
from aiohttp import ClientSession
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import WSGITransport
from main import app
import asyncio


class ResponseMock:
    def __init__(self, data, *args, **kwargs):
        self.data = data

    def __call__(self, *args, **kwargs):
        return self

    async def read(self):
        return self.data

    @property
    def content(self):
        return self

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args, **kwargs):
        pass


class ResponseMockCounter(ResponseMock):
    def __init__(self, data, *args, **kwargs):
        self.data = data
        self.counter = 0

    def __call__(self, *args, **kwargs):
        self.counter += 1
        return self


@pytest_asyncio.fixture
async def sms_activate(request):
    service = SMSActivateService()
    await service.connect()
    yield service
    await service.close()

@pytest.mark.asyncio
async def test_get_balance(monkeypatch, sms_activate):
    server_response = b'ACCESS_BALANCE:32.42'
    monkeypatch.setattr(ClientSession, "get", ResponseMock(server_response))
    assert (await sms_activate.get_balance()) == 32.42

@pytest.mark.asyncio
async def test_result_is_cached(monkeypatch, sms_activate):
    mock = ResponseMockCounter('''{
    "0": {
        "id": 0,
        "rus": "Россия",
        "eng": "Russia",
        "chn": "俄罗斯",
        "visible": 1,
        "retry": 1,
        "rent": 1,
        "multiService": 1
    }}'''.encode('utf-8'))
    monkeypatch.setattr(ClientSession, "get", mock)
    await sms_activate.get_countries()
    assert mock.counter == 1
    await sms_activate.get_countries()
    assert mock.counter == 1

@pytest.mark.asyncio
async def test_server_raise_exception(monkeypatch, sms_activate):
    monkeypatch.setattr(ClientSession, "get", ResponseMock(b"{}"))
    with pytest.raises(ServerUnavailable):
        await sms_activate.get_price("0", 'tg')

client = TestClient(app)

async def mail():
    await asyncio.sleep(10)
    client.post("/sms_activate_webhook", json={"activationId": 123456,"service": "go","text": "SMS test",
                "code": "Your sms code","country": 0,"receivedAt": "2022-06-01 17:30:57",})

class ServerWebhookMock(ResponseMock):
    def __init__(self):
        self.sms_sent: str = None  #  Текст смс, показывает что хендлер был вызван

    def __call__(self, url: str, params: dict[str, str]):
        if params['action'] == 'getCountries':
            self.data = '''{"0": {"id": 0,"rus": "Россия","eng": "Russia","chn": "俄罗斯",
                        "visible": 1,"retry": 1,"rent": 1,"multiService": 1}}'''.encode('utf-8')
        elif params['action'] == 'getNumberV2':
            self.data = '''{
                      "activationId": 123456,
                      "phoneNumber": "+79000000000",
                      "activationCost": "12.50",
                      "countryCode": "0",
                      "canGetAnotherSms": "1",
                      "activationTime": "2022-06-01 17:30:57",
                      "activationOperator": "mtt"
                    }'''.encode()
            asyncio.create_task(mail())  # Отправляет запрос на вебхукы через 10 секунд
        return self

    async def read(self):
        return self.data


async def callback(text: str, server: ServerWebhookMock):
    server.sms_sent = text

@pytest.mark.asyncio
async def test_webhook(monkeypatch, sms_activate):
    mock =  ServerWebhookMock()
    monkeypatch.setattr(ClientSession, "get", mock)
    telephone_number = await sms_activate.rent_number("0", "go", callback, server=mock)
    assert telephone_number == '+79000000000'
    assert mock.sms_sent is None
    await asyncio.sleep(20)
    assert mock.sms_sent == "SMS test"