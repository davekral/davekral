#include <QApplication>
#include "MyWidget.h"

int main(int argc, char *argv[]) {
    QApplication app(argc, argv);

    RocketWidget widget;
    widget.resize(1000, 600);
    widget.show();

    return app.exec();
}
