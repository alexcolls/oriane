import { handler } from './index';

const codes = [
  "DI5RZbSTV-t",
  "DGRChv1Mzvz",
  "DGLWBwutOMf",
  "DF9t1vuoxgm",
  "DF74Pw_q6pL",
  "DF32H4aywnq",
  "DF6AYXrSTrV",
  "DF4H3PZOdwF",
  "DEsqQ3wS8BE",
];

// Create a test event with one SQS record per shortcode
const testEvent = {
  Records: codes.map((code) => ({
    body: JSON.stringify({
      shortcode: code,
      platform: 'instagram',
      frame_interval: 1, // 1 frame per second (by default)
    }),
  })),
};

async function runTest() {
  try {
    console.log('Starting test...');
    const result = await handler(testEvent as any);
    console.log('Test result:', JSON.stringify(result, null, 2));
  } catch (error) {
    console.error('Test failed:', error);
  }
}

runTest();
