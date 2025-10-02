"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.getSscdLambdaExpCost = void 0;
const getSscdLambdaExpCost = (num_of_videos) => {
    const num_of_vid_per_lambda = 10;
    const avg_duration_per_lambda = 53.2;
    const num_of_gb_per_sec = 3;
    const cost_gb_per_sec = 0.0000166667;
    return ((num_of_videos / num_of_vid_per_lambda) *
        avg_duration_per_lambda *
        num_of_gb_per_sec *
        cost_gb_per_sec);
};
exports.getSscdLambdaExpCost = getSscdLambdaExpCost;
//# sourceMappingURL=utils.js.map