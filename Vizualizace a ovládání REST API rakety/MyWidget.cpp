#include "MyWidget.h"
#include <QPainter>
#include <QNetworkRequest>
#include <QNetworkAccessManager>
#include <QNetworkReply>
#include <QJsonDocument>
#include <QKeyEvent>
#include <QLineEdit>
#include <QJsonObject>
#include <QMouseEvent>
#include <QDebug>

RocketWidget::RocketWidget(QWidget *parent)
    : QWidget(parent), networkManager(new QNetworkAccessManager(this)) {
    // Výchozí nastavení
    sceneWidth = 1000;
    sceneHeight = 600;
    controlsHeight = 150; // Výška oblasti ovládacích prvků
    launchpadOffset = 50;

    QUrl url("http://localhost:8008/api/data/rocket/Rocket?data&mime=application/json");
    QNetworkRequest request(url);

    QNetworkReply *reply = networkManager->get(request);
    connect(reply, &QNetworkReply::finished, this, [this, reply]() {
        if (reply->error() == QNetworkReply::NoError) {
            serverConnected = false;
        }
        else{
            serverConnected = true;
        }
    });

    // Hlavní rozvržení
    QVBoxLayout *mainLayout = new QVBoxLayout(this);

    // Text nad scénou
    QLabel *headerLabel = new QLabel("Vizualizace rakety", this);
    headerLabel->setAlignment(Qt::AlignCenter); // Zarovnání na střed
    headerLabel->setStyleSheet("font-size: 16px; font-weight: bold;"); // Styling
    mainLayout->addWidget(headerLabel); // Přidání textu do layoutu

    // Stav připojení
    connectionStatusLabel = new QLabel("Nepřipojeno", this);
    connectionStatusLabel->setAlignment(Qt::AlignCenter);
    connectionStatusLabel->setStyleSheet("font-size: 14px; color: red;");
    mainLayout->addWidget(connectionStatusLabel);

    // Scéna (vykresluje se přímo v RocketWidget)
    sceneWidget = new QWidget(this);
    sceneWidget->setSizePolicy(QSizePolicy::Expanding, QSizePolicy::Expanding);
    mainLayout->addWidget(sceneWidget);

    // Spodní oblast obsahující ovládání a informace
    QWidget *bottomWidget = new QWidget(this);
    QVBoxLayout *bottomLayout = new QVBoxLayout(bottomWidget);

    // Čára oddělující scénu od spodní oblasti
    QFrame *line = new QFrame(this);
    line->setFrameShape(QFrame::HLine);
    line->setFrameShadow(QFrame::Sunken);
    bottomLayout->addWidget(line);

    // Vytvoření rozvržení pro ovládací prvky
    QWidget *controlsWidget = new QWidget(this);
    QHBoxLayout *controlsLayout = new QHBoxLayout(controlsWidget);

    // Reset button
    resetButton = new QPushButton("Reset", this);
    controlsLayout->addWidget(resetButton);
    connect(resetButton, &QPushButton::clicked, this, &RocketWidget::resetRocket);

    // Levá tryska
    leftThrusterButton = new QPushButton("Left Thruster (OFF)", this);
    controlsLayout->addWidget(leftThrusterButton);
    connect(leftThrusterButton, &QPushButton::clicked, this, [this]() {
        toggleThruster("http://localhost:8008/api/data/rocket/CNB_left_thruster:YCN?data&mime=application/json", leftThrusterActive);
    });

    // Pravá tryska
    rightThrusterButton = new QPushButton("Right Thruster (OFF)", this);
    controlsLayout->addWidget(rightThrusterButton);
    connect(rightThrusterButton, &QPushButton::clicked, this, [this]() {
        toggleThruster("http://localhost:8008/api/data/rocket/CNB_right_thruster:YCN?data&mime=application/json", rightThrusterActive);
    });

    // Slider pro hlavní motor
    mainEngineSlider = new QSlider(Qt::Horizontal, this);
    mainEngineSlider->setRange(0, 2);
    controlsLayout->addWidget(mainEngineSlider);
    connect(mainEngineSlider, &QSlider::valueChanged, this, [this](int value) {
        double power = value;
        sendControlCommand("http://localhost:8008/api/data/rocket/CNR_EngineThrottle:ycn?data&mime=application/json", QJsonObject{{"v", power}});
    });

    // Textová pole pro nastavení šířky a výšky
    QLabel *widthLabel = new QLabel("Scene Width:", this);
    controlsLayout->addWidget(widthLabel);

    widthInput = new QLineEdit(QString::number(sceneWidth), this);
    controlsLayout->addWidget(widthInput);

    updateWidthButton = new QPushButton("Update Width", this);
    controlsLayout->addWidget(updateWidthButton);
    connect(updateWidthButton, &QPushButton::clicked, this, [this]() {
        bool ok;
        int newWidth = widthInput->text().toInt(&ok);
        if (ok && newWidth > 0) {
            sendControlCommand("http://localhost:8008/api/data/rocket/Rocket:Width?data&mime=application/json", QJsonObject{{"v", newWidth}});
            sceneWidth = newWidth;
            update();
        }
    });

    QLabel *heightLabel = new QLabel("Scene Height:", this);
    controlsLayout->addWidget(heightLabel);

    heightInput = new QLineEdit(QString::number(sceneHeight), this);
    controlsLayout->addWidget(heightInput);

    updateHeightButton = new QPushButton("Update Height", this);
    controlsLayout->addWidget(updateHeightButton);
    connect(updateHeightButton, &QPushButton::clicked, this, [this]() {
        bool ok;
        int newHeight = heightInput->text().toInt(&ok);
        if (ok && newHeight > 0) {
            sendControlCommand("http://localhost:8008/api/data/rocket/Rocket:Height?data&mime=application/json", QJsonObject{{"v", newHeight}});
            sceneHeight = newHeight;
            update();
        }
    });
    enableControls(false);
    bottomLayout->addWidget(controlsWidget);

    // Přidání oblasti pro informace
    QWidget *infoWidget = new QWidget(this);
    QGridLayout *infoLayout = new QGridLayout(infoWidget);

    // Vytvoření štítků pro každou informaci
    xLabel = new QLabel("X: 0.00", this);
    infoLayout->addWidget(xLabel, 0, 0);
    yLabel = new QLabel("Y: 0.00", this);
    infoLayout->addWidget(yLabel, 0, 1);

    rotationLabel = new QLabel("Rotation: 0.00°", this);
    infoLayout->addWidget(rotationLabel, 1, 0);
    mainEngineLabel = new QLabel("Engine Throttle: 0", this);
    infoLayout->addWidget(mainEngineLabel, 1, 1);

    leftThrusterLabel = new QLabel("Left Thruster: OFF", this);
    infoLayout->addWidget(leftThrusterLabel, 2, 0);
    rightThrusterLabel = new QLabel("Right Thruster: OFF", this);
    infoLayout->addWidget(rightThrusterLabel, 2, 1);

    touchdownLabel = new QLabel("Touchdown: No", this);
    infoLayout->addWidget(touchdownLabel, 3, 0);
    crashedLabel = new QLabel("Crashed: No", this);
    infoLayout->addWidget(crashedLabel, 3, 1);

    // Popisky pro VX a VY
    vxLabel = new QLabel("VX: 0.0", this);
    infoLayout->addWidget(vxLabel, 1, 4);

    vyLabel = new QLabel("VY: 0.0", this);
    infoLayout->addWidget(vyLabel, 1, 6);

    // Bar grafy pro VX a VY
    vxBar = new BarGraphWidget(this);
    vxBar->setFixedSize(20, 60); // Malý sloupeček
    infoLayout->addWidget(vxBar, 1, 3);

    vyBar = new BarGraphWidget(this);
    vyBar->setFixedSize(20, 60); // Malý sloupeček
    infoLayout->addWidget(vyBar, 1, 5);

    bottomLayout->addWidget(infoWidget);

    // Přidání spodní části do hlavního layoutu
    mainLayout->addWidget(bottomWidget);

    // Nastavení hlavního layoutu
    setLayout(mainLayout);

    // Periodická kontrola serveru
    connect(&timer, &QTimer::timeout, this, &RocketWidget::checkServerConnection);
    timer.start(1000); // Kontrola každou sekundu

    // Časovač pro pravidelné získávání dat z API
    connect(&timer, &QTimer::timeout, this, &RocketWidget::fetchDataFromApi);
    timer.start(50); // Aktualizace každých 50 ms

    // Počáteční hodnoty
    x = -static_cast<double>(sceneWidth / 2) + launchpadOffset + 25;
    y = 0;

    // První ruční načtení dat z API
    fetchDataFromApi();
}



// Konstruktor
BarGraphWidget::BarGraphWidget(QWidget *parent)
    : QWidget(parent), vx(0), vy(0) {}

// Nastavení dat a překreslení grafu
void BarGraphWidget::setData(double newVx, double newVy) {
    vx = newVx;
    vy = newVy;
    update(); // Překreslení grafu
}

// Vykreslení grafu
void BarGraphWidget::paintEvent(QPaintEvent *event) {
    QPainter painter(this);
    painter.setRenderHint(QPainter::Antialiasing);

    int width = this->width();
    int height = this->height();
    int barWidth = width;

    // Vypočítání výšky sloupců na základě aktuálních hodnot
    double maxVelocity = 30.0; // Maximální rychlost
    int vxHeight = static_cast<int>((qAbs(vx) / maxVelocity) * height);
    int vyHeight = static_cast<int>((qAbs(vy) / maxVelocity) * height);

    // Vykreslení pozadí
    painter.setBrush(Qt::lightGray);
    painter.drawRect(0, 0, width, height);

    // Vykreslení sloupce pro VX
    painter.setBrush(Qt::blue);
    painter.drawRect(0, height - vxHeight, barWidth, vxHeight);

    // Vykreslení sloupce pro VY
    painter.setBrush(Qt::green);
    painter.drawRect(0, height - vyHeight, barWidth, vyHeight);
}


void RocketWidget::paintEvent(QPaintEvent *event) {
    QPainter painter(this);
    painter.setRenderHint(QPainter::Antialiasing);

    // Přizpůsobení měřítka scény
    double scaleX = static_cast<double>(sceneWidget->width()) / sceneWidth;
    double scaleY = static_cast<double>(sceneWidget->height()) / sceneHeight;
    double scale = qMin(scaleX, scaleY); // Zachování poměru stran

    // Posun na střed scény (spodní část)
    double centerX = sceneWidget->geometry().x() + sceneWidget->width() / 2.0;
    double centerY = sceneWidget->geometry().y() + sceneWidget->height();
    painter.translate(centerX, centerY);

    // Aplikace jednotného měřítka
    painter.scale(scale, -scale); // Inverze Y osy

    // Nastavení maskování: pouze viditelná část scény
    painter.setClipRect(-sceneWidth / 2, 0, sceneWidth, sceneHeight);

    // Kreslení pozadí scény
    painter.setBrush(Qt::white);
    painter.drawRect(-sceneWidth / 2, 0, sceneWidth, sceneHeight);

    // Kreslení plošin (startovací plošiny)
    painter.setBrush(Qt::blue);
    int padWidth = 50;  // Šířka plošin
    int padHeight = 20; // Výška plošin

    // Levá plošina
    int leftPadCenterX = -sceneWidth / 2 + launchpadOffset; // Střed levé plošiny
    int leftPadX = leftPadCenterX - padWidth / 2;           // Levý okraj plošiny
    painter.drawRect(leftPadX, 0, padWidth, padHeight);

    // Pravá plošina
    int rightPadCenterX = sceneWidth / 2 - launchpadOffset; // Střed pravé plošiny
    int rightPadX = rightPadCenterX - padWidth / 2;         // Levý okraj plošiny
    painter.drawRect(rightPadX, 0, padWidth, padHeight);

    // Kreslení rakety
    painter.save();
    double rocketX = x;   // Dynamická X-ová pozice rakety
    double rocketY = y + 15; // Posun pro správný střed rotace rakety
    painter.translate(rocketX, rocketY);
    painter.rotate(rotation);

    // Tělo rakety
    QRectF rocketBody(-12, -15, 24, 48);
    painter.setBrush(Qt::red);
    painter.drawRect(rocketBody);

    // Hlavní motor (plamen)
    painter.setBrush(Qt::yellow);
    int flameHeight = (mainEnginePower == 1) ? 10 : (mainEnginePower == 2) ? 20 : 0;
    painter.drawRect(-5, -15, 10, -flameHeight);

    // Postranní trysky
    if (leftThrusterActive) {
        painter.setBrush(Qt::yellow);
        painter.drawEllipse(QPointF(-15, 27), 5, 5);
    }
    if (rightThrusterActive) {
        painter.setBrush(Qt::yellow);
        painter.drawEllipse(QPointF(15, 27), 5, 5);
    }

    painter.restore();

    // Vykreslení šipky rychlosti
    drawVelocityArrow(painter, vx, -vy);

    // Obnovení maskování
    painter.setClipping(false);
}

bool RocketWidget::isRocketOutOfScene() {
    if (ignoreCollisions) {
        return false; // Ignorujeme kolize během resetu
    }

    // Souřadnice středu rakety
    double centerX = x;
    double centerY = y + 24; // Posun na střed rakety

    // Rozměry rakety
    double halfWidth = 12;  // Poloviční šířka
    double halfHeight = 24; // Poloviční výška

    // Vypočítání rohů rakety s ohledem na rotaci
    double radians = rotation * M_PI / 180.0; // Převod na radiány
    double cosTheta = cos(radians);
    double sinTheta = sin(radians);

    // Rohy rakety relativně k jejímu středu
    QPointF topLeft(-halfWidth, halfHeight);
    QPointF topRight(halfWidth, halfHeight);
    QPointF bottomLeft(-halfWidth, -halfHeight);
    QPointF bottomRight(halfWidth, -halfHeight);

    // Rotace rohů podle úhlu rotace rakety
    QPointF rotatedTopLeft(
        cosTheta * topLeft.x() - sinTheta * topLeft.y() + centerX,
        sinTheta * topLeft.x() + cosTheta * topLeft.y() + centerY);
    QPointF rotatedTopRight(
        cosTheta * topRight.x() - sinTheta * topRight.y() + centerX,
        sinTheta * topRight.x() + cosTheta * topRight.y() + centerY);
    QPointF rotatedBottomLeft(
        cosTheta * bottomLeft.x() - sinTheta * bottomLeft.y() + centerX,
        sinTheta * bottomLeft.x() + cosTheta * bottomLeft.y() + centerY);
    QPointF rotatedBottomRight(
        cosTheta * bottomRight.x() - sinTheta * bottomRight.y() + centerX,
        sinTheta * bottomRight.x() + cosTheta * bottomRight.y() + centerY);

    // Kontrola, zda kterýkoliv roh opustil hranice scény
    auto isOutOfScene = [this](const QPointF &point) {
        return point.x() < -sceneWidth / 2 || point.x() > sceneWidth / 2 || 
               point.y() < 0 || point.y() > sceneHeight;
    };

    if (isOutOfScene(rotatedTopLeft) || isOutOfScene(rotatedTopRight) ||
        isOutOfScene(rotatedBottomLeft) || isOutOfScene(rotatedBottomRight)) {
        if (!crashed) { // Nastavíme crashed pouze při prvním nárazu
            crashed = true;
            qDebug() << "Raketa narazila do hranic scény.";
        }
        return true;
    }

    return false;
}




void RocketWidget::checkServerConnection() {
    QUrl url("http://localhost:8008/api/data/rocket/Rocket?data&mime=application/json");
    QNetworkRequest request(url);

    // Optional: Add authentication headers if needed
    QString username = "admin";
    QString password = ""; // Replace with actual password if required
    QString credentials = username + ":" + password;
    QByteArray authHeader = credentials.toLocal8Bit().toBase64();
    request.setRawHeader("Authorization", "Basic " + authHeader);
    request.setRawHeader("Content-Type", "application/json");

    QNetworkReply *reply = networkManager->get(request);
    connect(reply, &QNetworkReply::finished, this, &RocketWidget::checkApiResponse);
}

void RocketWidget::checkApiResponse() {
    QNetworkReply *reply = qobject_cast<QNetworkReply *>(sender());
    if (!reply) {
        qDebug() << "Chyba: Nelze získat QNetworkReply.";
        return;
    }

    if (reply->error() == QNetworkReply::NoError) {
        QByteArray response = reply->readAll();
        QJsonDocument jsonDoc = QJsonDocument::fromJson(response);

        if (!jsonDoc.isNull() && jsonDoc.isObject()) {
            QJsonObject jsonObject = jsonDoc.object();
            QJsonArray subitems = jsonObject["subitems"].toArray();

            bool xFound = false;

            for (const QJsonValue &value : subitems) {
                QJsonObject obj = value.toObject();
                if (obj.contains("X")) {
                    x = obj["X"].toObject()["v"].toDouble();
                    xFound = true; // Hodnota X byla nalezena
                    break;
                }
            }

            if (xFound) {
                // Server je připojen
                if (!serverConnected) {
                    enableControls(true);
                    serverConnected = true;
                    connectionStatusLabel->setText("Připojeno");
                    connectionStatusLabel->setStyleSheet("font-size: 14px; color: green;");
                    qDebug() << "Server připojen: Hodnota X nalezena (" << x << ")";
                }
            } else {
                // Hodnota X nebyla nalezena, server je nepřipojen
                if (serverConnected) {
                    enableControls(false);
                    serverConnected = false;
                    connectionStatusLabel->setText("Nepřipojeno");
                    connectionStatusLabel->setStyleSheet("font-size: 14px; color: red;");
                    qDebug() << "Server nepřipojen: Hodnota X nebyla nalezena.";
                }
            }
        } else {
            // JSON není platný objekt, server je nepřipojen
            if (serverConnected) {
                enableControls(false);
                serverConnected = false;
                connectionStatusLabel->setText("Nepřipojeno");
                connectionStatusLabel->setStyleSheet("font-size: 14px; color: red;");
                qDebug() << "Server nepřipojen: JSON odpověď není platná.";
            }
        }
    } else {
        // Chyba při připojení
        if (serverConnected) {
            enableControls(false);
            serverConnected = false;
            connectionStatusLabel->setText("Nepřipojeno");
            connectionStatusLabel->setStyleSheet("font-size: 14px; color: red;");
        }
        qDebug() << "Chyba připojení k serveru:" << reply->errorString();
    }

    reply->deleteLater();
}










void RocketWidget::enableControls(bool enable) {
        resetButton->setEnabled(enable);
        leftThrusterButton->setEnabled(enable);
        rightThrusterButton->setEnabled(enable);
        mainEngineSlider->setEnabled(enable);

        resetButton->setEnabled(enable);
        leftThrusterButton->setEnabled(enable);
        rightThrusterButton->setEnabled(enable);
        mainEngineSlider->setEnabled(enable);

        // Vstupy pro šířku a výšku scény
        widthInput->setEnabled(enable);
        heightInput->setEnabled(enable);
        updateWidthButton->setEnabled(enable);
        updateHeightButton->setEnabled(enable);
    
}


void RocketWidget::initializeSceneFromServer() {
    qDebug() << "Inicializace scény z dat serveru...";
    fetchDataFromApi(); // Zavoláme ruční načtení dat
}

void RocketWidget::fetchDataFromApi() {

    if (crashed) {
        return; // Zastavení aktualizace
    }

    QUrl url("http://localhost:8008/api/data/rocket/Rocket?data&mime=application/json");
    QNetworkRequest request(url);

    // Optional: Add authentication headers if needed
    QString username = "admin";
    QString password = ""; // Replace with actual password if required
    QString credentials = username + ":" + password;
    QByteArray authHeader = credentials.toLocal8Bit().toBase64();
    request.setRawHeader("Authorization", "Basic " + authHeader);
    request.setRawHeader("Content-Type", "application/json");

    QNetworkReply *reply = networkManager->get(request);
    connect(reply, &QNetworkReply::finished, this, &RocketWidget::handleApiResponse);
}

void RocketWidget::handleApiResponse() {

    if (crashed) {
       // qDebug() << "Kolize detekována, API data neaktualizována.";
        return; // Zastavení aktualizace
    }

    QNetworkReply *reply = qobject_cast<QNetworkReply *>(sender());
    if (reply->error() == QNetworkReply::NoError) {
        QByteArray response = reply->readAll();
        QJsonDocument jsonDoc = QJsonDocument::fromJson(response);
        QJsonObject jsonObject = jsonDoc.object();

        // Zpracování odpovědi (parsování dat)
        QJsonArray subitems = jsonObject["subitems"].toArray();
        for (const QJsonValue &value : subitems) {
            QJsonObject obj = value.toObject();
            if (obj.contains("X")) {
                x = obj["X"].toObject()["v"].toDouble();
            }
            if (obj.contains("Y")) {
                y = obj["Y"].toObject()["v"].toDouble();
            }
            if (obj.contains("Rotation")) {
                rotation = obj["Rotation"].toObject()["v"].toDouble() * 180 / 3.14159265; // Radians to degrees
            }
            if (obj.contains("VX")) {
                vx = obj["VX"].toObject()["v"].toDouble();
            }
            if (obj.contains("VY")) {
                vy = obj["VY"].toObject()["v"].toDouble();
            }
            if (obj.contains("EngineThrottle")) {
                mainEnginePower = obj["EngineThrottle"].toObject()["v"].toDouble();
            }
            if (obj.contains("LeftThruster")) {
                leftThrusterActive = obj["LeftThruster"].toObject()["v"].toBool();
            }
            if (obj.contains("RightThruster")) {
                rightThrusterActive = obj["RightThruster"].toObject()["v"].toBool();
            }
            if (obj.contains("Touchdown")) {
                touchdown = obj["Touchdown"].toObject()["v"].toBool();
            }
            if (obj.contains("Crashed")) {
                crashed = obj["Crashed"].toObject()["v"].toBool();
            }
            if (obj.contains("LaunchpadOffset")) {
                launchpadOffset = obj["LaunchpadOffset"].toObject()["v"].toDouble();
            }
            if (obj.contains("Width")) {
                sceneWidth = obj["Width"].toObject()["v"].toInt();
            }
            if (obj.contains("Height")) {
                sceneHeight = obj["Height"].toObject()["v"].toInt();
            }
        }

        // Kontrola, zda raketa překročila hranice scény
        if (isRocketOutOfScene()) {
            //qDebug() << "Raketa narazila do hranic scény!";
            crashed = true; // Nastavení stavu rakety na "crash"
        }
    } else {
        qDebug() << "API Error:" << reply->errorString();
    }

    // Aktualizace QLabelů
    xLabel->setText(QString("X: %1").arg(x, 0, 'f', 2));
    yLabel->setText(QString("Y: %1").arg(y, 0, 'f', 2));
    rotationLabel->setText(QString("Rotation: %1°").arg(rotation, 0, 'f', 2));
    mainEngineLabel->setText(QString("Engine Throttle: %1").arg(mainEnginePower, 0, 'f', 1));
    leftThrusterLabel->setText(QString("Left Thruster: %1").arg(leftThrusterActive ? "ON" : "OFF"));
    rightThrusterLabel->setText(QString("Right Thruster: %1").arg(rightThrusterActive ? "ON" : "OFF"));
    touchdownLabel->setText(QString("Touchdown: %1").arg(touchdown ? "Yes" : "No"));
    crashedLabel->setText(QString("Crashed: %1").arg(crashed ? "Yes" : "No"));
    vxLabel->setText(QString("VX: %1").arg(vx, 0, 'f', 2));
    vyLabel->setText(QString("VY: %1").arg(vy, 0, 'f', 2));
    vxBar->setData(vx, 0); // Pouze VX
    vyBar->setData(0, vy); // Pouze VY

    update(); // Trigger repaint
    reply->deleteLater();
}


void RocketWidget::sendControlCommand(const QString &url, const QJsonObject &payload) {
    qDebug() << "Sending POST request to URL:" << url;
    qDebug() << "Payload being sent:" << QString(QJsonDocument(payload).toJson(QJsonDocument::Indented));

    QNetworkRequest request(url);

    // Nastavení hlaviček
    QString username = "admin";
    QString password = "";
    QString concatenated = username + ":" + password;
    QByteArray data = concatenated.toLocal8Bit().toBase64();
    QString headerData = "Basic " + data;

    request.setRawHeader("Authorization", headerData.toLocal8Bit());
    request.setRawHeader("Content-Type", "application/json");

    // SSL konfigurace
    QSslConfiguration conf = request.sslConfiguration();
    conf.setPeerVerifyMode(QSslSocket::VerifyNone);
    request.setSslConfiguration(conf);

    // Ruční sestavení payloadu
    QString payloadString = "{";
    payloadString += "\"v\":";
    payloadString += QString::number(payload["v"].toDouble());
    payloadString += "}";

    // Odeslání POST požadavku
    QNetworkReply* reply = networkManager->post(request, payloadString.toUtf8());

    // Správa odpovědi
    connect(reply, &QNetworkReply::readyRead, this, [reply]() {
        QByteArray response = reply->readAll();
        qDebug() << "POST Request Successful. Response:" << QString(response);
        reply->deleteLater();
    });

    connect(reply, &QNetworkReply::errorOccurred, this, [reply](QNetworkReply::NetworkError code) {
        qDebug() << "POST Request Error:" << code << "-" << reply->errorString();
        reply->deleteLater();
    });

    qDebug() << "POST Request Sent to" << url << "with payload" << payloadString;
}

void RocketWidget::resetRocket() {
    // První reset
    qDebug() << "Provádí se první reset.";
    sendControlCommand("http://localhost:8008/api/data/rocket/MP_reset:BSTATE?data&mime=application/json", QJsonObject{{"v", 1}});

    QTimer::singleShot(100, [this]() {
        sendControlCommand("http://localhost:8008/api/data/rocket/MP_reset:BSTATE?data&mime=application/json", QJsonObject{{"v", 0}});
    });

    // Druhý reset po krátké pauze
    QTimer::singleShot(200, [this]() {
        qDebug() << "Provádí se druhý reset.";
        sendControlCommand("http://localhost:8008/api/data/rocket/MP_reset:BSTATE?data&mime=application/json", QJsonObject{{"v", 1}});

        QTimer::singleShot(100, [this]() {
            sendControlCommand("http://localhost:8008/api/data/rocket/MP_reset:BSTATE?data&mime=application/json", QJsonObject{{"v", 0}});
        });

        // Nastavení lokálního stavu rakety
        crashed = false;
        x = -static_cast<double>(sceneWidth / 2) + launchpadOffset + 25; // Výchozí X-ová pozice
        y = 0;                                                          // Výchozí Y-ová pozice
        rotation = 0;                                                   // Žádná rotace
        mainEnginePower = 0;                                            // Motor vypnutý
        leftThrusterActive = false;                                     // Levá tryska vypnutá
        rightThrusterActive = false;                                    // Pravá tryska vypnutá

        // Aktualizace QLabelů
        xLabel->setText("X: 0.00");
        yLabel->setText("Y: 0.00");
        rotationLabel->setText("Rotation: 0.00°");
        mainEngineLabel->setText("Engine Throttle: 0");
        leftThrusterLabel->setText("Left Thruster: OFF");
        rightThrusterLabel->setText("Right Thruster: OFF");
        crashedLabel->setText("Crashed: No");

        // Překreslení scény
        update();
        qDebug() << "Raketa byla úspěšně resetována (druhý reset dokončen).";
    });
}





void RocketWidget::toggleThruster(const QString &url, bool &thrusterState) {
    thrusterState = !thrusterState; // Přepnutí stavu
    sendControlCommand(url, QJsonObject{{"v", thrusterState ? 1 : 0}});
    qDebug() << (thrusterState ? "Thruster ON" : "Thruster OFF") << "for URL:" << url;

    // Změna textu tlačítka
    if (url.contains("CNB_left_thruster")) {
        leftThrusterButton->setText(thrusterState ? "Left Thruster (ON)" : "Left Thruster (OFF)");
    } else if (url.contains("CNB_right_thruster")) {
        rightThrusterButton->setText(thrusterState ? "Right Thruster (ON)" : "Right Thruster (OFF)");
    }
}

void RocketWidget::drawVelocityArrow(QPainter &painter, double vx, double vy) {
    const int arrowSize = 50; // Maximální délka šipky
    const double maxVelocity = 20.0; // Normovací konstanta pro maximální rychlost

    // Výpočet velikosti a směru šipky
    double magnitude = sqrt(vx * vx + vy * vy); // Velikost rychlosti
    double normalizedVx = (magnitude > 0) ? (vx / magnitude) : 0.0;
    double normalizedVy = (magnitude > 0) ? (vy / magnitude) : 0.0;

    double arrowLength = std::min(magnitude / maxVelocity, 1.0) * arrowSize;

    // Nastavení počátečního bodu (vpravo vedle hodnot)
    QPointF startPoint(-sceneWidth/2 + 50, sceneHeight-50); // Posun vpravo od hodnot
    QPointF endPoint(startPoint.x() + normalizedVx * arrowLength, 
                     startPoint.y() - normalizedVy * arrowLength); // Inverze Y osy

    // Vykreslení šipky
    QPen arrowPen(Qt::black, 2);
    painter.setPen(arrowPen);
    painter.drawLine(startPoint, endPoint);

    // Vykreslení hlavy šipky
    const double arrowHeadSize = 10.0; // Velikost šipky na konci
    QPointF arrowHead1(endPoint.x() - normalizedVx * arrowHeadSize - normalizedVy * arrowHeadSize / 2,
                       endPoint.y() + normalizedVy * arrowHeadSize - normalizedVx * arrowHeadSize / 2);
    QPointF arrowHead2(endPoint.x() - normalizedVx * arrowHeadSize + normalizedVy * arrowHeadSize / 2,
                       endPoint.y() + normalizedVy * arrowHeadSize + normalizedVx * arrowHeadSize / 2);

    QPolygonF arrowHead;
    arrowHead << endPoint << arrowHead1 << arrowHead2;

    painter.setBrush(Qt::black);
    painter.drawPolygon(arrowHead);
}

void RocketWidget::keyPressEvent(QKeyEvent *event) {
    // Pokud server není připojen, ignorujeme klávesové vstupy
    if (!serverConnected) {
        return;
    }

    if (event->key() == Qt::Key_W) {
        wPressed = true; // Označíme, že W je stisknuté
        if (shiftPressed) { // Pokud je Shift také stisknutý
            mainEnginePower = 2.0;
        } else { // Pokud Shift není stisknutý
            mainEnginePower = 1.0;
        }
        sendControlCommand("http://localhost:8008/api/data/rocket/CNR_EngineThrottle:ycn?data&mime=application/json",
                           QJsonObject{{"v", mainEnginePower}});
    } else if (event->key() == Qt::Key_Shift) {
        shiftPressed = true; // Označíme, že Shift je stisknutý
        if (wPressed) { // Pokud je W také stisknuté
            mainEnginePower = 2.0; // Zvýšíme výkon
            sendControlCommand("http://localhost:8008/api/data/rocket/CNR_EngineThrottle:ycn?data&mime=application/json",
                               QJsonObject{{"v", mainEnginePower}});
        }
    } else if (event->key() == Qt::Key_S) { // Snížení výkonu
        mainEnginePower = 0.0;
        sendControlCommand("http://localhost:8008/api/data/rocket/CNR_EngineThrottle:ycn?data&mime=application/json",
                           QJsonObject{{"v", mainEnginePower}});
    } else if (event->key() == Qt::Key_A) { // Aktivace levé trysky
        leftThrusterActive = true;
        sendControlCommand("http://localhost:8008/api/data/rocket/CNB_left_thruster:YCN?data&mime=application/json",
                           QJsonObject{{"v", 1}});
    } else if (event->key() == Qt::Key_D) { // Aktivace pravé trysky
        rightThrusterActive = true;
        sendControlCommand("http://localhost:8008/api/data/rocket/CNB_right_thruster:YCN?data&mime=application/json",
                           QJsonObject{{"v", 1}});
    } else {
        QWidget::keyPressEvent(event); // Zachová výchozí chování pro ostatní klávesy
    }

    // Překreslení scény po změně
    update();
}

void RocketWidget::keyReleaseEvent(QKeyEvent *event) {
    // Pokud server není připojen, ignorujeme klávesové vstupy
    if (!serverConnected) {
        return;
    }

    if (event->key() == Qt::Key_W) { // Uvolnění W
        wPressed = false; // Označíme, že W již není stisknuté
        mainEnginePower = 0.0; // Nastavíme výkon na 0
        sendControlCommand("http://localhost:8008/api/data/rocket/CNR_EngineThrottle:ycn?data&mime=application/json",
                           QJsonObject{{"v", mainEnginePower}});
    } else if (event->key() == Qt::Key_Shift) { // Uvolnění Shift
        shiftPressed = false; // Označíme, že Shift již není stisknutý
        if (wPressed) { // Pokud je stále stisknuté W
            mainEnginePower = 1.0; // Vrátíme výkon zpět na 1
            sendControlCommand("http://localhost:8008/api/data/rocket/CNR_EngineThrottle:ycn?data&mime=application/json",
                               QJsonObject{{"v", mainEnginePower}});
        }
    } else if (event->key() == Qt::Key_A) { // Deaktivace levé trysky
        leftThrusterActive = false;
        sendControlCommand("http://localhost:8008/api/data/rocket/CNB_left_thruster:YCN?data&mime=application/json",
                           QJsonObject{{"v", 0}});
    } else if (event->key() == Qt::Key_D) { // Deaktivace pravé trysky
        rightThrusterActive = false;
        sendControlCommand("http://localhost:8008/api/data/rocket/CNB_right_thruster:YCN?data&mime=application/json",
                           QJsonObject{{"v", 0}});
    } else if (event->key() == Qt::Key_R) { // Uvolnění klávesy R
        resetRocket(); // Zavolání metody pro reset rakety
    } else {
        QWidget::keyReleaseEvent(event); // Zachová výchozí chování pro ostatní klávesy
    }

    // Překreslení scény po změně
    update();
}
