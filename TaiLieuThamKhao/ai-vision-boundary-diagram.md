# AI Vision Service – Service Boundary Diagram

## 1. High-Level Boundary Diagram

```mermaid
flowchart TB
    subgraph Upstream
        CAM["📷 Camera Stream"]
    end
    
    subgraph "AI Vision Service"
        API["POST /api/v1/detect"]
        VAL["Validator"]
        PRE["Preprocessor"]
        AI["YOLOv8 Model"]
        POST["Result Formatter"]
        LOG["Logger"]
        REDIS["Redis Cache"]
    end
    
    subgraph Downstream
        CB["⚙️ Core Business"]
        NOT["🔔 Notification"]
        MON["📊 Monitoring"]
    end
    
    CAM -->|"1. image_url"| API
    API --> VAL
    VAL -->|"valid"| PRE
    VAL -->|"invalid"| ERR["❌ Error"]
    PRE -->|"processed"| AI
    AI -->|"detections"| POST
    POST -->|"2. result"| CB
    POST --> LOG
    LOG -->|"3. metadata"| MON
    CB -->|"4. decision"| NOT
    ERR -.->|"error"| CAM
    
    style CAM fill:#ffcccc
    style CB fill:#ccffcc
    style NOT fill:#ccffcc
    style MON fill:#ccffcc
    style API fill:#bbf
    style VAL fill:#bbf
    style PRE fill:#bbf
    style AI fill:#bbf
    style POST fill:#bbf
    style LOG fill:#dfd
    style REDIS fill:#dfd
    style ERR fill:#fcc
```

---

## 2. Detailed Flow Diagram

```mermaid
sequenceDiagram
    participant CAM as Camera Stream
    participant API as API Gateway
    participant VAL as Validator
    participant PRE as Preprocessor
    participant AI as AI Model
    participant CB as Core Business
    participant LOG as Logger
    
    rect lightblue
        Note over CAM,LOG: Happy Path
        CAM->>API: POST /detect
        API->>VAL: Validate schema
        VAL->>PRE: OK
        PRE->>AI: Preprocessed tensor
        AI->>CB: {detections[]}
        AI->>LOG: Log metadata
        CB-->>CAM: 200 OK
    end
    
    rect lightpink
        Note over CAM,CB: Error Path
        CAM->>API: POST /detect
        API->>VAL: Validate
        VAL-->>API: Invalid
        API-->>CAM: 400 Bad Request
    end
```

---

## 3. Architecture Overview

```mermaid
flowchart LR
    subgraph External
        C1["Camera 1"]
        C2["Camera 2"]
        CB["Core Business"]
        NT["Notification"]
    end
    
    subgraph "AI Vision Service"
        LB["Load Balancer"]
        GW["API Gateway"]
        SVC["Detection Service"]
        AI["YOLOv8 Model"]
        QM["Queue Manager"]
    end
    
    subgraph Infra
        RD["Redis"]
        MON["Prometheus/Grafana"]
    end
    
    C1 & C2 --> LB
    LB --> GW
    GW --> SVC
    SVC --> AI
    SVC --> RD
    SVC --> QM
    QM --> NT
    SVC --> MON
    
    style C1 fill:#ffcccc
    style C2 fill:#ffcccc
    style CB fill:#ccffcc
    style NT fill:#ccffcc
    style AI Vision Service fill:#bbf,stroke:#333,stroke-width:3px
    style LB fill:#bbf
    style GW fill:#bbf
    style SVC fill:#bbf
    style AI fill:#bbf
    style QM fill:#bbf
    style RD fill:#dfd
    style MON fill:#dfd
```

---

## 4. Contract Definition

```mermaid
flowchart TB
    subgraph Input
        I1["camera_id (required)"]
        I2["image_url (required)"]
        I3["timestamp (required)"]
        I4["model_version (optional)"]
    end
    
    subgraph Service["AI Vision Service"]
        PROC["Processing Pipeline"]
    end
    
    subgraph Output
        O1["detection_id"]
        O2["detections[]"]
        O3["model_version"]
        O4["processing_time_ms"]
    end
    
    I1 & I2 & I3 & I4 --> PROC
    PROC --> O1 & O2 & O3 & O4
    
    style I1 fill:#ffcccc
    style I2 fill:#ffcccc
    style I3 fill:#ffcccc
    style I4 fill:#ffe6cc
    style O1 fill:#ccffcc
    style O2 fill:#ccffcc
    style O3 fill:#ccffcc
    style O4 fill:#ccffcc
```

---

## 5. Downstream Impact Assessment

```mermaid
flowchart LR
    CHANGE["API/Event Change"]
    
    subgraph Consumers
        CB1["Core Business"]
        CB2["Notification"]
        CB3["Monitoring"]
    end
    
    subgraph Migration
        M1["Update clients"]
        M2["Version bump"]
        M3["Test"]
    end
    
    CHANGE --> CB1
    CHANGE --> CB2
    CHANGE --> CB3
    CB1 & CB2 & CB3 --> M1 --> M2 --> M3
    
    style CHANGE fill:#fcc
    style CB1 fill:#ccffcc
    style CB2 fill:#ccffcc
    style CB3 fill:#ccffcc
```

---

## Legend

| Symbol | Meaning |
|--------|---------|
| 📷 | Upstream / Actor |
| ⚙️ | Downstream / Consumer |
| 🔔 | External Service |
| 📊 | Monitoring |
| ➡️ | Sync call |
| -.- | Async call |
| 🔴 | Error path |
| 🔵 | Internal service |
| 🟢 | Downstream |
| 🟡 | Input (optional) |

---

## Data Flow Summary

```
┌─────────────────────────────────────────────────────────────────────┐
│                        AI Vision Service                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   UPSTREAM              INTERNAL                  DOWNSTREAM        │
│       │                     │                          │             │
│   Camera ──────▶ API ───▶ Validator ───▶ YOLOv8 ──────▶ Core        │
│   Stream            │           │                       │            │
│       │            │           ▼                       │            │
│       │        Invalid    Preprocess                   │            │
│       │            │           │                       ▼            │
│       ◀────────────┘           ▼               Notification       │
│     400 Error           Result Formatter                            │
│                              │                                      │
│                              ▼                                      │
│                         Redis/Logs                                  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```
