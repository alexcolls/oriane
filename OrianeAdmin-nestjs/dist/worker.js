"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const core_1 = require("@nestjs/core");
const app_module_1 = require("./app.module");
async function bootstrap() {
    const appContext = await core_1.NestFactory.createApplicationContext(app_module_1.AppModule);
    console.log('Worker started – processing Bull jobs.');
    return appContext;
}
bootstrap();
//# sourceMappingURL=worker.js.map