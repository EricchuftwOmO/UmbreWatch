# UmbreWatch：智慧傘架防盜系統

結合 Edge-Fog-Cloud IoT 架構的智慧傘架，透過人臉識別防止雨傘被盜，並提供即時監控與數據分析。

## 系統架構

| 層級 | 硬體 / 軟體 | 功能 |
|------|------------|------|
| **邊緣層（Edge）** | Raspberry Pi + GrovePi HAT | 超聲波感測器偵測傘槽佔用狀態；PIR 感測器偵測顧客離開；蜂鳴器與 LED 警報 |
| **霧層（Fog）** | PC（本 Python 腳本） | MQTT Broker；DeepFace 本地人臉識別，零註冊防盜驗證 |
| **雲端層（Cloud）** | InfluxDB + Grafana + Azure OpenAI | 資料儲存、儀表板視覺化、LLM 圖像分析 |

## 硬體接線

**Slot 1（槽位 1）**
- 超聲波感測器 → Digital port 8
- 綠色 LED → Digital port 6
- 紅色 LED → Digital port 4

**Slot 2（槽位 2）**
- 超聲波感測器 → Digital port 7
- 綠色 LED → Digital port 5
- 紅色 LED → Digital port 3

**共用**
- 蜂鳴器 → Digital port 2

## 安裝與設定

### 1. 匯入 Node-RED 流程
將 `node-red-flow.json` 匯入 Node-RED：
1. 在瀏覽器開啟 Node-RED（`http://<RaspberryPi_IP>:1880`）
2. 點擊右上角選單 → **Import**
3. 選擇本 repo 的 `node-red-flow.json` 並點擊 **Import**

### 2. 設定 IP 位址
請依照自己的網路環境修改以下設定：

- `smartUmbrellaRackEn.py`：將 `INFLUX_HOST` 改為你的 Raspberry Pi IP。
- Node-RED MQTT broker 節點：Server 改為你的 PC IP。
- Node-RED InfluxDB 節點：Host 改為你的 Raspberry Pi IP。
- Grafana → Connections → Data Sources → DB → URL：改為 `http://<RaspberryPi_IP>:8086`。

### 3. 設定 API 金鑰
`node-red-flow.json` 中的 API 金鑰已替換為佔位符，請填入自己的金鑰：
- **Node-RED「Send Picture To LLM」節點**：將 `YOUR_AZURE_OPENAI_API_KEY` 替換為你的 Azure OpenAI API 金鑰。
- **Node-RED「set zip code」節點**：將 `YOUR_OPENWEATHER_API_KEY` 替換為你的 OpenWeather API 金鑰。

### 4. 建立 Azure OpenAI 服務
在 Azure 上部署 OpenAI 資源，以啟用 LLM 圖像推理功能（分析照片中人物是否表現緊張）。

### 5. 啟動 MQTT Broker（在 PC 上執行）
```powershell
cd "C:\Program Files\Mosquitto"
.\mosquitto_sub.exe -h localhost -t "umbrella/slot1/photo" -v
```

### 6. 執行霧層 Python 腳本
```powershell
# 啟動虛擬環境
.\venv\Scripts\Activate.ps1

# 執行防盜主程式
python .\smartUmbrellaRackEn.py
```

系統啟動時會從 InfluxDB 還原槽位記憶，接著監聽 MQTT 圖像訊息。放傘時儲存主人照片；取傘時用 DeepFace 進行人臉比對，若不符則發布 `umbrella/alarm` 訊息觸發所有警報。

## Grafana 儀表板

| 儀表板 | 內容 |
|--------|------|
| Dashboard 1 | 槽位狀態與資料分析 |
| Dashboard 2 | Azure OpenAI 圖像說明（LLM 分析） |
| Dashboard 3 | 雲端服務使用量統計 |

## 人臉參考照片

將自己的人臉照片（`.jpg` / `.png`）放入 `my_faces/` 資料夾，供 DeepFace 建立身份資料庫。**請勿將個人照片上傳至 Git。**

## 相依套件

請在 Python 虛擬環境中安裝：

```
paho-mqtt
deepface
influxdb
```

DeepFace 另需 `tensorflow`、`opencv-python` 與 `dlib`。

## 專案文件

- [`docs/ProjectPaper.pdf`](docs/ProjectPaper.pdf) — IEEE 格式研究論文
- [`docs/Poster.pptx`](docs/Poster.pptx) — 專題海報
- [`docs/README.pdf`](docs/README.pdf) — 含截圖的原始設定說明
