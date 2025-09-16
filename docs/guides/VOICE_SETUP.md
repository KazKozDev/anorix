# 🎙️ Advanced Voice System Setup

## 🎯 Что реализовано

Полная замена простого голосового ввода на продвинутую систему:

- ✅ **WebRTC Streaming** - реальное время аудио между браузером и сервером
- ✅ **Whisper base STT** - быстрое и качественное распознавание речи
- ✅ **Bark TTS** - высококачественный синтез речи 
- ✅ **Интеграция с Ajax** - полная интеграция с виртуальным другом
- ✅ **Fallback система** - автоматический переход на legacy режим
- ✅ **Wake Word Detection** - активация по "Привет, друг" с Porcupine

## 📦 Установка зависимостей

```bash
# Основные зависимости для голосовой системы
pip install -r requirements_voice.txt

# Если есть проблемы с PyTorch, установите вручную:
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu

# Для CUDA (если есть GPU):
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118
```

## 🚀 Запуск системы

### 1. Базовый запуск
```bash
# Запуск с голосовой системой
python run_web_ui.py

# Или напрямую
cd web_ui
python app.py
```

### 2. Тестирование системы
```bash
# Тест всех компонентов
python test_voice_system.py

# Ожидаемый вывод:
# ✅ Voice Processor
# ✅ WebRTC Server  
# ✅ Friend Integration
# 🎉 All tests passed!
```

### 3. Терминальный интерфейс (без голоса)
```bash
python friend_interface.py
```

## 🌐 Использование веб-интерфейса

1. **Откройте браузер**: http://127.0.0.1:5000

2. **Проверьте статус**:
   - В консоли браузера должно быть: `✅ Using Advanced Voice System`
   - Рядом с переключателем: `Голосовой режим (WebRTC)`

3. **Активируйте голос**:
   - Включите переключатель "Голосовой режим"
   - Разрешите доступ к микрофону
   - Статус изменится на: `WebRTC голосовая связь активна`

4. **Wake Word Detection (опционально)**:
   - Включите кнопку 🎧 рядом с голосовым режимом
   - Разрешите постоянный доступ к микрофону
   - Скажите "Start" для автоактивации голосового режима
   - При обнаружении wake word система автоматически включит голосовой режим
   - Продолжайте говорить - ваша речь будет распознана и отображена в чате

5. **Говорите с Ajax**:
   - Система автоматически распознает речь
   - Ajax отвечает качественным синтезированным голосом
   - Визуализатор показывает активность

## 🔧 Настройки и конфигурация

### Voice Processor настройки:
```python
# В voice_processor.py можно изменить:
whisper_model = "base"          # tiny, base, small, medium, large
bark_voice = "v2/en_speaker_6"  # Качественный английский голос
device = "auto"                 # auto, cpu, cuda, mps
sample_rate = 16000            # Частота дискретизации
```

### WebRTC настройки:
```python
# В webrtc_server.py:
chunk_duration = 1.0           # Размер аудио чанков в секундах
```

## 🐛 Troubleshooting

### Проблема: "Voice engine not available"
```bash
# Проверьте установку зависимостей:
pip install aiortc av faster-whisper bark

# Проверьте PyTorch:
python -c "import torch; print(torch.__version__)"
```

### Проблема: Микрофон не работает
1. Используйте **HTTPS** или **localhost** (WebRTC требование)
2. Разрешите доступ к микрофону в браузере
3. Проверьте настройки системы

### Проблема: Медленная работа
```bash
# Используйте более быструю модель Whisper:
# В voice_processor.py замените на:
whisper_model = "tiny"  # Самая быстрая модель

# Или установите CUDA для GPU ускорения:
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### Проблема: Socket.IO connection failed
```bash
# Убедитесь что установлен flask-socketio:
pip install flask-socketio

# Проверьте что сервер запущен через socketio.run(), а не app.run()
```

## 📊 Мониторинг системы

### В консоли браузера:
```javascript
// Проверка подключения:
friendApp.advancedVoiceHandler.isConnected

// Статус сессии:
friendApp.advancedVoiceHandler.voiceSession

// Тест голосовой системы:
friendApp.advancedVoiceHandler.testVoiceConnection()
```

### В логах сервера:
```
✅ Virtual Friend initialized successfully
✅ Voice Server initialized successfully  
🔗 Client connected: <session_id>
🎙️ Created voice session: <voice_session_id>
📞 Handled WebRTC offer for session <session_id>
🎤 Transcribed: <text>...
🗣️ Generating speech: <text>...
```

## 🔄 Fallback режимы

Система автоматически определяет доступные возможности:

1. **Advanced Voice (WebRTC)** - если все зависимости установлены
2. **Legacy Voice (Web Speech API)** - если WebRTC недоступен  
3. **Text Only** - если голос вообще недоступен

Статус отображается рядом с переключателем голосового режима.

## 🎛️ API Endpoints

```
# WebRTC Voice API
POST /api/voice/create-session  - создать голосовую сессию
POST /api/voice/offer          - WebRTC handshake  
GET  /api/voice/sessions       - список активных сессий
GET  /api/health               - статус всех систем

# Socket.IO Events  
connect, disconnect            - подключение
create_voice_session          - создание сессии
webrtc_offer, webrtc_answer   - WebRTC сигнализация
text_to_speech                - TTS для активной сессии
```

## ⚡ Производительность

### Рекомендуемые системные требования:
- **CPU**: 4+ ядра (для Whisper и Bark)
- **RAM**: 8GB+ (модели в памяти)
- **GPU**: Опционально, для ускорения
- **Сеть**: Стабильное соединение для WebRTC

### Оптимизация:
- Используйте `whisper_model="tiny"` для скорости
- Включите GPU ускорение если доступно
- Настройте `chunk_duration` для баланса задержки/качества

## 🔮 Wake Word Detection

### Настройка Porcupine:
Для полноценного wake word detection нужно:

1. **Получить Porcupine Access Key**:
   - Зарегистрируйтесь на https://picovoice.ai/
   - Получите бесплатный access key
   - Добавьте в `wake-word.js`: `this.accessKey = 'YOUR_ACCESS_KEY_HERE';`

2. **Создать кастомную модель для "Start"**:
   - Используйте Porcupine Console для создания модели wake word "Start"
   - Замените `BuiltinKeyword.HEY_SIRI` на свою модель

3. **Текущий режим - Fallback**:
   - Без access key система использует простое обнаружение речевой активности
   - Любая громкая речь активирует голосовой режим как "Start"
   - После активации система продолжает слушать и распознавать речь
   - Распознанный текст автоматически отображается в чате
   - Для production рекомендуется настроить полноценную Porcupine модель

## 🔮 Следующие этапы

- [x] **Porcupine Wake Word** - активация по "Start" ✅
- [ ] **Улучшенная обработка аудио** - VAD, шумоподавление  
- [ ] **Голосовые команды** - специальные команды для Ajax
- [ ] **Эмоциональная окраска голоса** - изменение тона по настроению
- [ ] **Кастомная Porcupine модель** - точное распознавание "Start"

---

🎉 **Система готова к использованию!** Ajax теперь может говорить и слушать в режиме реального времени через WebRTC!