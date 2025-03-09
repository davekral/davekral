#ifndef ROCKETWIDGET_H
#define ROCKETWIDGET_H

#include <QWidget>
#include <QSlider>
#include <QTimer>
#include <QLabel>
#include <QLineEdit>
#include <QNetworkAccessManager>
#include <QPushButton>
#include <QVBoxLayout>
#include <QKeyEvent>
#include <QJsonObject>
#include <QJsonArray>

// Třída pro vykreslování barového grafu
class BarGraphWidget : public QWidget {
    Q_OBJECT

public:
    explicit BarGraphWidget(QWidget *parent = nullptr);
    void setData(double newVx, double newVy);

protected:
    void paintEvent(QPaintEvent *event) override;

private:
    double vx;
    double vy;
};

// Třída pro hlavní ovládání rakety
class RocketWidget : public QWidget {
    Q_OBJECT

public:
    explicit RocketWidget(QWidget *parent = nullptr);

protected:
    void paintEvent(QPaintEvent *event) override;
    void keyPressEvent(QKeyEvent *event) override;
    void keyReleaseEvent(QKeyEvent *event) override;

private slots:
    void fetchDataFromApi();
    void drawVelocityArrow(QPainter &painter, double vx, double vy);
    void handleApiResponse();
    void resetRocket(); // Nová metoda pro reset rakety
    void sendControlCommand(const QString &url, const QJsonObject &payload); // Odeslání příkazů na API
    void toggleThruster(const QString &url, bool &thrusterState);
    void checkServerConnection();       // Kontrola stavu připojení k serveru
    void enableControls(bool enable);   // Povolení/zakázání ovládacích prvků
    void initializeSceneFromServer();   // Inicializace scény z dat serveru
    bool isRocketOutOfScene();
    void checkApiResponse();

private:
    QNetworkAccessManager *networkManager; // Správce pro REST API
    QTimer timer; // Časovač pro pravidelné aktualizace

    // UI Elements
    QVBoxLayout *layout;       // Rozvržení
    QPushButton *resetButton;  // Tlačítko pro reset
    QPushButton *leftThrusterButton;  // Tlačítko pro levý motor
    QPushButton *rightThrusterButton; // Tlačítko pro pravý motor
    QSlider *mainEngineSlider;        // Slider pro výkon hlavního motoru
    QWidget *sceneWidget; // Widget pro vykreslení scény
    QWidget *controlsWidget; // Widget pro ovládací prvky
    QLabel *apiDataLabel; // Popisek pro zobrazení dat z API
    QLineEdit *widthInput;   // Textové pole pro šířku scény
    QLineEdit *heightInput;  // Textové pole pro výšku scény
    QPushButton *updateWidthButton;
    QPushButton *updateHeightButton;
    bool serverConnected; // Stav serveru
    QLabel *connectionStatusLabel; // Zobrazení stavu připojení

    // Nový widget pro barový graf
    BarGraphWidget *barGraphWidget;

    // Rocket parameters
    double x = 0;             
    double y = 0;             
    double rotation = 0;      
    double vx = 0;            
    double vy = 0;            
    double mainEnginePower = 0; 
    bool leftThrusterActive = false;  
    bool rightThrusterActive = false; 
    bool touchdown = false;   
    bool crashed = false;     
    double launchpadOffset = 0; 
    int sceneWidth = 1000;    
    int sceneHeight = 600;    

    bool shiftPressed = false; // Indikátor, zda je Shift stisknutý
    bool wPressed = false;     // Indikátor, zda je W stisknuté
    bool ignoreCollisions = false; // Ignorovat kolize při resetu
    int controlsHeight; // Výška části s ovládacími prvky
    QLabel *xLabel;
    QLabel *yLabel;
    QLabel *rotationLabel;
    QLabel *mainEngineLabel;
    QLabel *leftThrusterLabel;
    QLabel *rightThrusterLabel;
    QLabel *touchdownLabel;
    QLabel *crashedLabel;
    QLabel *vxLabel; 
    QLabel *vyLabel; 
    BarGraphWidget *vxBar; // Graf pro VX
    BarGraphWidget *vyBar; // Graf pro VY
};

#endif // ROCKETWIDGET_H
