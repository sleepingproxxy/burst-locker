from abc import ABC, abstractmethod
import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import time
from dataclasses import dataclass, field, asdict
import random
import json
import hashlib
import requests
import asyncio
import argparse
import subprocess
from telethon import TelegramClient, functions, types
from telethon.errors import SessionPasswordNeededError
from stem import Signal
from stem.control import Controller
from fake_useragent import UserAgent
from typing import Any, Optional, List, Dict, Union
import logging
import sys
from pathlib import Path




logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)



@dataclass
class TorConfig:
    host: str = "127.0.0.1"
    port: int = 9050
    control_port: int = 9051
    password: Optional[str] = None
    interval: int = 10
    use: bool = False
    
    @property
    def proxies(self) -> Dict[str, str]:
        return {
            'http': f'socks5://{self.host}:{self.port}',
            'https': f'socks5://{self.host}:{self.port}'
        }

class TorSwitcher:
    def __init__(self, config: TorConfig):
        self.config = config
        self.ua = UserAgent()
        self.last_switch = 0
        
    def switch_ip(self) -> bool:
        try:
            with Controller.from_port(port=self.config.control_port) as controller:
                if self.config.password:
                    controller.authenticate(password=self.config.password)
                else:
                    controller.authenticate()
                
                controller.signal(Signal.NEWNYM)
                self.ua.random()
                self.last_switch = time.time()
                logger.info("IP и UserAgent успешно сменен через Tor")
                return True
                
        except Exception as e:
            logger.error(f"Ошибка смены IP или UserAgent через Tor: {str(e)}")
            return False
    
    async def auto_switch(self, interval: int = None):
        interval = interval or self.config.interval
        while True:
            await asyncio.sleep(interval)
            await self.switch_ip()

class IPChecker:
    def __init__(self, tor_config: TorConfig):
        self.tor_config = tor_config
        self.ua = UserAgent()
        
        
    
    def get_current_ip(self, method: str = 'api') -> Optional[str]:
        headers = {'User-Agent': self.ua.random} 
        
        proxies = self.tor_config.proxies if self.tor_config.use else None
        
        methods = {
            'api': ('https://check.torproject.org/api/ip', lambda r: r.json()['IP']),
            'ident': ('https://ident.me', lambda r: r.text.strip()),
            'httpbin': ('https://httpbin.org/ip', lambda r: r.json()['origin']),
            'ipify': ('https://api.ipify.org?format=json', lambda r: r.json()['ip'])
        }
        
        if method not in methods:
            logger.error(f"Неизвестный метод: {method}")
            return None
        
        url, parser = methods[method]
        
        try:
            response = requests.get(url, proxies=proxies, headers=headers, timeout=10)
            try:
                response.raise_for_status()
                ip = parser(response)
                logger.info(f"Текущий IP ({method}): {ip}")
                return ip
            finally:
                response.close
        except Exception as e:
            logger.error(f"Ошибка получения IP методом {method}: {str(e)}")
            return None
    def __del__(self):
        self.session.close()


@dataclass
class Config:
    
    net_conf: TorConfig = field(default_factory=TorConfig)
    user_conf: List[Dict[str, Any]] = field(default_factory=list)
    ad_conf: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Config':
        
        config = cls()
        
        if 'net_conf' in data and data['net_conf']:
            net_data = data['net_conf']
            config.net_conf = TorConfig(
                host=net_data.get('host', '127.0.0.1'),
                port=net_data.get('port', 9050),
                control_port=net_data.get('control_port', 9051),
                password=net_data.get('password'),
                interval=net_data.get('interval', 10),
                use=net_data.get('use', False)
            )
        
        if 'user_conf' in data:
            config.user_conf = data['user_conf']
        
        if 'ad_conf' in data:
            config.ad_conf = data['ad_conf']
        
        return config
    
    def to_dict(self) -> Dict[str, Any]:
        
        return {
            'net_conf': asdict(self.net_conf),
            'user_conf': self.user_conf,
            'ad_conf': self.ad_conf
        }
    
    def update_from_dict(self, data: Dict[str, Any]) -> None:
        
        if 'net_conf' in data and data['net_conf']:
            net_data = data['net_conf']
            self.net_conf.host = net_data.get('host', self.net_conf.host)
            self.net_conf.port = net_data.get('port', self.net_conf.port)
            self.net_conf.control_port = net_data.get('control_port', self.net_conf.control_port)
            self.net_conf.password = net_data.get('password', self.net_conf.password)
            self.net_conf.interval = net_data.get('interval', self.net_conf.interval)
            self.net_conf.use = net_data.get('use', self.net_conf.use)
        
        if 'user_conf' in data:
            self.user_conf = data['user_conf']
        
        if 'ad_conf' in data:
            self.ad_conf = data['ad_conf']


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SessionManager:
    
    
    def __init__(self, password: str = None, salt: bytes = None):
        
        self.salt = salt
        self.key = self._generate_key(password)
        self.cipher = Fernet(self.key)
        self.sessions: Dict[str, bytes] = {}
        
        logger.info(f"SessionManager инициализирован. Ключ: {self.key[:10]}...")
    
    def _generate_key(self, password: str = None) -> bytes:
        
        if password is not None:
           
            if self.salt is None:
                self.salt = os.urandom(16)
                logger.info(f"Сгенерирована новая соль: {base64.b64encode(self.salt)[:10]}...")
            
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,  
                salt=self.salt,
                iterations=100000  # Исправлено: iterations, а не iteration
            )
            
            
            derived_key = kdf.derive(password.encode())
            key = base64.urlsafe_b64encode(derived_key)
            
        else:
            
            key = Fernet.generate_key()
            logger.info(f"Сгенерирован случайный ключ{key}")
        
        return key
    
    def get_salt(self) -> Optional[bytes]:
        
        return self.salt
    
    def get_key(self) -> bytes:
        
        return self.key
    
    def encrypt_session(self, session_data: bytes) -> bytes:
        
        if not isinstance(session_data, bytes):
            raise TypeError("session_data должен быть bytes")
        
        encrypted = self.cipher.encrypt(session_data)
        logger.debug(f"Зашифровано {len(session_data)} байт -> {len(encrypted)} байт")
        return encrypted
    
    def decrypt_session(self, encrypted_data: bytes) -> bytes:
        
        if not isinstance(encrypted_data, bytes):
            raise TypeError("encrypted_data должен быть bytes")
        
        try:
            decrypted = self.cipher.decrypt(encrypted_data)
            logger.debug(f"Расшифровано {len(encrypted_data)} байт -> {len(decrypted)} байт")
            return decrypted
        except Exception as e:
            logger.error(f"Ошибка при дешифровании: {e}")
            raise ValueError("Не удалось расшифровать данные") from e
    
    
class DataWorker:
    
    
    def __init__(self, config: Optional[Config] = None, path:str = None):
        self.config = config or Config()
        self.data_dir = Path("Your/path//to/data")
        self.data_dir.mkdir(exist_ok=True)
        
       
        self.targets_file = self.data_dir / "targets.txt"
        self.sessions_file = self.data_dir / "sessions.json"
        self.net_file = self.data_dir / "net_config.json"
        self.config_file = self.data_dir / "config.json"
    
    def load_all(self) -> Config:
        
        
        targets = self._load_targets()
        sessions = self._load_sessions()
        net_config = self._load_net_config()
        saved_config = self._load_config()
        
       
        if saved_config:
            self.config.update_from_dict(saved_config)
        
        if net_config:
            self.config.update_from_dict({'net_conf': net_config})
        
        
        if sessions:
            user_conf = []
            for phone, data in sessions.items():
                user_conf.append({
                    'phone': phone,
                    'api_id': data.get('api_id'),
                    'api_hash': data.get('api_hash')
                })
            self.config.user_conf = user_conf
        
        return self.config
    
    def save_all(self) -> None:
        
        if hasattr(self, '_current_targets'):
            self._save_targets(self._current_targets)
        
       
        self._save_config(self.config.to_dict())
        
        
        self._save_net_config(asdict(self.config.net_conf))
        
        
        if self.config.user_conf:
            sessions = {}
            for user in self.config.user_conf:
                phone = user.get('phone')
                if phone:
                    sessions[phone] = {
                        'api_id': user.get('api_id'),
                        'api_hash': user.get('api_hash')
                    }
            self._save_sessions(sessions)
    
    def _load_targets(self) -> List[str]:
        
        targets = []
        if self.targets_file.exists():
            try:
                with open(self.targets_file, 'r', encoding='utf-8') as f:
                    targets = [line.strip() for line in f if line.strip()]
                logger.info(f"Загружено {len(targets)} целей")
            except Exception as e:
                logger.error(f"Ошибка загрузки целей: {e}")
        return targets
    
    def _save_targets(self, targets: List[str]) -> None:
        
        try:
            with open(self.targets_file, 'w', encoding='utf-8') as f:
                for target in targets:
                    f.write(f"{target}\n")
            logger.info(f"Сохранено {len(targets)} целей")
        except Exception as e:
            logger.error(f"Ошибка сохранения целей: {e}")
    
    def _load_sessions(self) -> Dict[str, Any]:
        
        sessions = {}
        if self.sessions_file.exists():
            try:
                with open(self.sessions_file, 'r', encoding='utf-8') as f:
                    sessions = json.load(f)
                logger.info(f"Загружено {len(sessions)} сессий")
            except Exception as e:
                logger.error(f"Ошибка загрузки сессий: {e}")
        return sessions
    
    def _save_sessions(self, sessions: Dict[str, Any]) -> None:
        
        try:
            with open(self.sessions_file, 'w', encoding='utf-8') as f:
                json.dump(sessions, f, ensure_ascii=False, indent=2)
            logger.info(f"Сохранено {len(sessions)} сессий")
        except Exception as e:
            logger.error(f"Ошибка сохранения сессий: {e}")
    
    def _load_net_config(self) -> Dict[str, Any]:
       
        net_config = {}
        if self.net_file.exists():
            try:
                with open(self.net_file, 'r', encoding='utf-8') as f:
                    net_config = json.load(f)
                logger.info("Сетевая конфигурация загружена")
            except Exception as e:
                logger.error(f"Ошибка загрузки сетевой конфигурации: {e}")
        return net_config
    
    def _save_net_config(self, net_config: Dict[str, Any]) -> None:
       
        try:
            with open(self.net_file, 'w', encoding='utf-8') as f:
                json.dump(net_config, f, ensure_ascii=False, indent=2)
            logger.info("Сетевая конфигурация сохранена")
        except Exception as e:
            logger.error(f"Ошибка сохранения сетевой конфигурации: {e}")
    
    def _load_config(self) -> Dict[str, Any]:
        
        config_data = {}
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                logger.info("Конфигурация загружена")
            except Exception as e:
                logger.error(f"Ошибка загрузки конфигурации: {e}")
        return config_data
    
    def _save_config(self, config_data: Dict[str, Any]) -> None:
       
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
            logger.info("Конфигурация сохранена")
        except Exception as e:
            logger.error(f"Ошибка сохранения конфигурации: {e}")
    
    def input_targets(self) -> List[str]:
        
        print("\nВведите цели (по одной на строку, пустая строка для завершения):")
        targets = []
        while True:
            line = input().strip()
            if not line:
                break
            targets.append(line)
        
        self._current_targets = targets
        self._save_targets(targets)
        return targets
    
    def input_sessions(self) -> List[Dict[str, Any]]:
       
        print("\nВведите данные сессий в формате 'phone:api_id:api_hash' (пустая строка для завершения):")
        sessions_dict = {}
        while True:
            line = input().strip()
            if not line:
                break
            parts = line.split(':')
            if len(parts) >= 3:
                phone = parts[0]
                try:
                    sessions_dict[phone] = {
                        'api_id': int(parts[1]),
                        'api_hash': parts[2]
                    }
                except ValueError:
                    logger.error(f"Неверный формат API ID для {phone}")
        
        
        user_conf = []
        for phone, data in sessions_dict.items():
            user_conf.append({
                'phone': phone,
                'api_id': data['api_id'],
                'api_hash': data['api_hash']
            })
        
        self.config.user_conf = user_conf
        self._save_sessions(sessions_dict)
        return user_conf
    
    def input_net_config(self) -> TorConfig:
        
        print("\nВведите сетевые настройки (или оставьте пустым для значений по умолчанию):")
        
        host = input(f"Host [{self.config.net_conf.host}]: ").strip()
        if host:
            self.config.net_conf.host = host
        
        port_str = input(f"Port [{self.config.net_conf.port}]: ").strip()
        if port_str:
            try:
                self.config.net_conf.port = int(port_str)
            except ValueError:
                logger.error("Неверный формат порта")
        
        control_port_str = input(f"Control port [{self.config.net_conf.control_port}]: ").strip()
        if control_port_str:
            try:
                self.config.net_conf.control_port = int(control_port_str)
            except ValueError:
                logger.error("Неверный формат control port")
        
        password = input(f"Password [{self.config.net_conf.password}]: ").strip()
        if password:
            self.config.net_conf.password = password
        
        interval_str = input(f"Interval [{self.config.net_conf.interval}]: ").strip()
        if interval_str:
            try:
                self.config.net_conf.interval = int(interval_str)
            except ValueError:
                logger.error("Неверный формат интервала")
        
        use_str = input(f"Use Tor (y/n) [{'y' if self.config.net_conf.use else 'n'}]: ").strip().lower()
        if use_str:
            self.config.net_conf.use = use_str.startswith('y')
        
        self._save_net_config(asdict(self.config.net_conf))
        return self.config.net_conf

    


class ReportData(ABC):
    reasons_list = [
        types.InputReportReasonChildAbuse(),
        types.InputReportReasonCopyright(),
        types.InputReportReasonFake(),
        types.InputReportReasonGeoIrrelevant(),
        types.InputReportReasonIllegalDrugs(),
        types.InputReportReasonOther(),
        types.InputReportReasonPersonalDetails(),
        types.InputReportReasonPornography(),
        types.InputReportReasonSpam(),
        types.InputReportReasonViolence()
    ]
    
    reason_map = {
        'child_abuse': 0, 'copyright': 1, 'fake': 2,
        'geo': 3, 'drugs': 4, 'other': 5,
        'personal': 6, 'porn': 7, 'spam': 8, 'violence': 9
    }
    
    def __init__(self, target: str, reason: str, count: int = 1):
        self.target = target
        self.reason = reason
        self.count = count
    
    @abstractmethod
    async def execute(self, client: TelegramClient) -> bool:
        pass

class SingleReporter(ReportData):
    async def execute(self, client: TelegramClient) -> bool:
        reason_index = self.reason_map.get(self.reason, 5)  # 5 = Other
        success = True
        
        for i in range(self.count):
            try:
                result = await client(functions.account.ReportPeerRequest(
                    peer=self.target,
                    reason=self.reasons_list[reason_index],
                    message=''
                ))
                logger.info(f"Жалоба {i+1}/{self.count} отправлена: {result}")
                await asyncio.sleep(0.5)
            except Exception as e:
                logger.error(f"Ошибка отправки жалобы: {e}")
                success = False
        
        return success

class BurstReporter(ReportData):
    async def execute(self, client: TelegramClient) -> bool:
        reasons = self.reason.split(',')
        success = True
        
        for reason in reasons:
            reason = reason.strip()
            if reason not in self.reason_map:
                logger.warning(f"Неизвестная причина: {reason}")
                continue
            
            reason_index = self.reason_map[reason]
            for i in range(self.count):
                try:
                    result = await client(functions.account.ReportPeerRequest(
                        peer=self.target,
                        reason=self.reasons_list[reason_index],
                        message=''
                    ))
                    logger.info(f"{reason}: жалоба {i+1}/{self.count}: {result}")
                    await asyncio.sleep(0.5)
                except Exception as e:
                    logger.error(f"Ошибка отправки {reason}: {e}")
                    success = False
        
        return success

class FullReporter(ReportData):
    async def execute(self, client: TelegramClient) -> bool:
        success = True
        
        for reason_name, reason_index in self.reason_map.items():
            for i in range(self.count):
                try:
                    result = await client(functions.account.ReportPeerRequest(
                        peer=self.target,
                        reason=self.reasons_list[reason_index],
                        message=''
                    ))
                    logger.info(f"{reason_name}: жалоба {i+1}/{self.count}: {result}")
                    await asyncio.sleep(0.5)
                except Exception as e:
                    logger.error(f"Ошибка отправки {reason_name}: {e}")
                    success = False
        
        return success

class Reporter:
    def __init__(self, strategy: ReportData):
        self.strategy = strategy
    
    async def run(self, client: TelegramClient) -> bool:
        return await self.strategy.execute(client)

class ClientsFabric:
    @staticmethod
    async def create_client(
        phone: str,
        api_id: int,
        api_hash: str,
        proxy: dict = None,
        session_path: str = "sessions"
    ) -> Optional[TelegramClient]:
        try:
            os.makedirs(session_path, exist_ok=True)
            session_file = os.path.join(session_path, phone.replace('+', ''))
            
            client = TelegramClient(session_file, api_id, api_hash, proxy=proxy)
            await client.connect()
            
            if not await client.is_user_authorized():
                await client.start(phone)
                code = input('Введите код из Telegram: ')
                
                try:
                    await client.start(phone, code)
                except SessionPasswordNeededError:
                    password = input('Введите пароль двухфакторной аутентификации: ')
                    await client.start(phone=phone,password=password)
            
            logger.info(f"Клиент для {phone} успешно создан")
            return client
            
        except Exception as e:
            logger.error(f"Ошибка создания клиента: {e}")
            return None
    
    @staticmethod
    async def client_connect(
        session_path: str,
        api_id: int,
        api_hash: str,
        proxy: dict = None,
        max_retries: int = 3
    ) -> Optional[TelegramClient]:
        for attempt in range(max_retries):
            try:
                client = TelegramClient(session_path, api_id, api_hash, proxy=proxy)
                await client.connect()
                
                if await client.is_user_authorized():
                    logger.info(f"Клиент {session_path} успешно подключен")
                    return client
                else:
                    logger.warning(f"Клиент {session_path} не авторизован")
                    await client.disconnect()
                    
                    phone = input(f"Введите номер телефона для {session_path}: ")
                    return await ClientsFabric.create_client(phone, api_id, api_hash, proxy)
                    
            except Exception as e:
                logger.error(f"Попытка {attempt + 1}/{max_retries} не удалась: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                else:
                    return None
        
        return None

def get_user_input(prompt: str, default: str = None) -> str:
    
    if default:
        value = input(f"{prompt} [{default}]: ").strip()
        return value if value else default
    else:
        return input(f"{prompt}: ").strip()

async def main():
    print("""
    ██████╗ ██╗   ██╗██████╗ ███████╗████████╗██╗      ██████╗  ██████╗██╗  ██╗███████╗██████╗ 
    ██╔══██╗██║   ██║██╔══██╗██╔════╝╚══██╔══╝██║     ██╔═══██╗██╔════╝██║ ██╔╝██╔════╝██╔══██╗
    ██████╔╝██║   ██║██████╔╝███████╗   ██║   ██║     ██║   ██║██║     █████╔╝ █████╗  ██████╔╝
    ██╔══██╗██║   ██║██╔══██╗╚════██║   ██║   ██║     ██║   ██║██║     ██╔═██╗ ██╔══╝  ██╔══██╗
    ██████╔╝╚██████╔╝██║  ██║███████║   ██║   ███████╗╚██████╔╝╚██████╗██║  ██╗███████╗██║  ██║
    ╚═════╝  ╚═════╝ ╚═╝  ╚═╝╚══════╝   ╚═╝   ╚══════╝ ╚═════╝  ╚═════╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝
    """)
    parser = argparse.ArgumentParser(description='Telegram Reporter')
    parser.add_argument('--config', '-c', type=str, default='data/config.json',
                       help='Путь к файлу конфигурации')
    parser.add_argument('--interactive', '-i', action='store_true',
                       help='Интерактивный режим ввода данных')
    parser.add_argument('--reason', '-r', type=str, default='other',
                       choices=['child_abuse', 'copyright', 'fake', 'geo', 
                               'drugs', 'other', 'personal', 'porn', 'spam', 'violence'],
                       help='Причина жалобы')
    parser.add_argument('--count', '-n', type=int, default=1,
                       help='Количество жалоб')
    parser.add_argument('--mode', '-m', type=str, default='single',
                       choices=['single', 'burst', 'full'],
                       help='Режим отправки жалоб')
    parser.add_argument('--tor', action='store_true',
                       help='Использовать Tor')
    
    args = parser.parse_args()
    
    try:
        data_worker = DataWorker()
        if args.interactive or not Path(args.config).exists():
            print("=== Интерактивный режим настройки ===")
            
            
            targets = data_worker.input_targets()
            if not targets:
                logger.error("Не введено ни одной цели")
                return
            
            
            sessions = data_worker.input_sessions()
            if not sessions:
                logger.error("Не введено ни одной сессии")
                return
            
            
            if args.tor:
                tor_config = data_worker.input_net_config()
            else:
                tor_config = TorConfig(use=False)
                data_worker.config.net_conf = tor_config
            
            
            data_worker.save_all()
        else:
            
            config = data_worker.load_all()
            targets = data_worker._load_targets()
            tor_config = config.net_conf
            
            if args.tor:
                tor_config.use = True
            
            if not targets:
                logger.error("Нет целей для обработки")
                return
            
            if not config.user_conf:
                logger.error("Нет сессий для обработки")
                return
        
        
        tor_switcher = None
        ip_checker = None
        
        if tor_config.use:
            ip_checker = IPChecker(tor_config)
            tor_switcher = TorSwitcher(tor_config)
            
            
            current_ip = ip_checker.get_current_ip()
            if current_ip:
                logger.info(f"Текущий IP через Tor: {current_ip}")
            else:
                logger.warning("Не удалось получить IP через Tor")
            asyncio.create_task(tor_switcher.auto_switch())
        clients = []
        proxy = tor_config.proxies if tor_config.use else None
        
        for user in data_worker.config.user_conf:
            phone = user.get('phone')
            api_id = user.get('api_id')
            api_hash = user.get('api_hash')
            
            if not all([phone, api_id, api_hash]):
                logger.warning(f"Неполные данные для пользователя: {user}")
                continue
            
            client = await ClientsFabric.create_client(
                phone=phone,
                api_id=api_id,
                api_hash=api_hash,
                proxy=proxy
            )
            
            if client:
                clients.append(client)
        
        if not clients:
            logger.error("Не удалось создать ни одного клиента")
            return
        
        logger.info(f"Создано {len(clients)} клиентов")
        for target in targets:
            logger.info(f"\n=== Обработка цели: {target} ===")
            
            
            if args.mode == 'single':
                report_strategy = SingleReporter(target, args.reason, args.count)
            elif args.mode == 'burst':
                report_strategy = BurstReporter(target, args.reason, args.count)
            elif args.mode == 'full':
                report_strategy = FullReporter(target, args.reason, args.count)
            else:
                logger.error(f"Неизвестный режим: {args.mode}")
                return
            
            reporter = Reporter(report_strategy)
            
            
            for i, client in enumerate(clients):
                logger.info(f"Клиент {i+1}/{len(clients)} отправляет жалобы...")
                
                try:
                    
                    if tor_config.use and tor_switcher and i > 0:
                        tor_switcher.switch_ip()
                        await asyncio.sleep(2)  # Ждем смену IP
                    
                    success = await reporter.run(client)
                    
                    if success:
                        logger.info(f"Клиент {i+1} успешно отправил жалобы")
                    else:
                        logger.warning(f"Клиент {i+1} отправил жалобы с ошибками")
                    
                    
                    if i < len(clients) - 1:
                        await asyncio.sleep(random.uniform(2, 5))
                        
                except Exception as e:
                    logger.error(f"Ошибка при работе с клиентом {i+1}: {e}")
            
            
            if target != targets[-1]:
                wait_time = random.uniform(5, 10)
                logger.info(f"Ожидание {wait_time:.1f} секунд перед следующей целью...")
                await asyncio.sleep(wait_time)
        
        logger.info("Все задачи выполнены")
        
    except KeyboardInterrupt:
        logger.info("Программа остановлена пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}", exc_info=True)
    finally:
        
        if 'clients' in locals():
            for client in clients:
                try:
                    await client.disconnect()
                except:
                    pass
        
        logger.info("Программа завершена")

if __name__ == "__main__":
    asyncio.run(main())
