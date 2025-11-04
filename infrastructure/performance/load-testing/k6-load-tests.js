/**
 * Production Load Testing Suite
 * Comprehensive load testing for insurance claims processing system
 */

import http from 'k6/http';
import { check, sleep, group } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';

// Custom metrics
export const errorRate = new Rate('errors');
export const claimProcessingTime = new Trend('claim_processing_time');
export const humanWorkflowLatency = new Trend('human_workflow_latency');
export const systemThroughput = new Counter('system_throughput');

// Test configuration for different scenarios
export const options = {
  scenarios: {
    // Baseline load test
    baseline_load: {
      executor: 'constant-vus',
      vus: 50,
      duration: '10m',
      tags: { scenario: 'baseline' },
    },

    // Peak load simulation
    peak_load: {
      executor: 'ramping-vus',
      startVUs: 50,
      stages: [
        { duration: '2m', target: 100 },
        { duration: '5m', target: 200 },
        { duration: '2m', target: 300 },
        { duration: '5m', target: 300 },
        { duration: '3m', target: 50 },
      ],
      tags: { scenario: 'peak' },
    },

    // Stress test
    stress_test: {
      executor: 'ramping-vus',
      startVUs: 100,
      stages: [
        { duration: '2m', target: 200 },
        { duration: '5m', target: 500 },
        { duration: '2m', target: 800 },
        { duration: '1m', target: 800 },
        { duration: '5m', target: 100 },
      ],
      tags: { scenario: 'stress' },
    },

    // Spike test
    spike_test: {
      executor: 'ramping-vus',
      startVUs: 50,
      stages: [
        { duration: '30s', target: 50 },
        { duration: '1m', target: 1000 },
        { duration: '30s', target: 50 },
      ],
      tags: { scenario: 'spike' },
    },

    // Soak test (endurance)
    soak_test: {
      executor: 'constant-vus',
      vus: 100,
      duration: '2h',
      tags: { scenario: 'soak' },
    },
  },

  thresholds: {
    // Performance requirements
    http_req_duration: ['p(95)<2000'], // 95% of requests under 2s
    http_req_failed: ['rate<0.01'],    // Error rate under 1%

    // Custom metric thresholds
    claim_processing_time: ['p(95)<5000'], // 95% processed under 5s
    human_workflow_latency: ['p(90)<1000'], // 90% routed under 1s
    errors: ['rate<0.05'], // Error rate under 5%
  },
};

// Test data generators
function generateClaimData() {
  const claimTypes = ['collision', 'comprehensive', 'liability', 'property'];
  const amounts = [5000, 15000, 25000, 50000, 75000, 100000];

  return {
    claim_id: `TEST-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
    policy_number: `POL-${Math.random().toString(36).substr(2, 8)}`,
    claim_amount: amounts[Math.floor(Math.random() * amounts.length)],
    claim_type: claimTypes[Math.floor(Math.random() * claimTypes.length)],
    description: 'Load test claim - damage to vehicle in parking lot incident',
    incident_date: new Date(Date.now() - Math.random() * 30 * 24 * 60 * 60 * 1000).toISOString(),
    reported_date: new Date().toISOString(),
    claimant_name: `Test Claimant ${Math.random().toString(36).substr(2, 5)}`,
    jurisdiction: ['CA', 'NY', 'FL', 'TX', 'IL'][Math.floor(Math.random() * 5)],
    vehicle_vin: `TEST${Math.random().toString(36).substr(2, 14).toUpperCase()}`,
    vehicle_year: 2015 + Math.floor(Math.random() * 9),
    vehicle_make: ['Toyota', 'Honda', 'Ford', 'BMW', 'Mercedes'][Math.floor(Math.random() * 5)],
  };
}

function generateUserCredentials() {
  const roles = ['claims_adjuster', 'senior_adjuster', 'underwriter', 'siu_investigator'];
  return {
    role: roles[Math.floor(Math.random() * roles.length)],
    license: `LIC-${Math.random().toString(36).substr(2, 8)}`,
    authority_level: [10000, 25000, 50000, 100000][Math.floor(Math.random() * 4)],
  };
}

// Base URL configuration
const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';
const API_ENDPOINTS = {
  coordinate: `${BASE_URL}/coordinate`,
  healthCheck: `${BASE_URL}/health`,
  workflowRoute: `${BASE_URL}/workflow/route-decision`,
  taskSubmit: `${BASE_URL}/workflow/submit-decision`,
  fraudAnalysis: `${BASE_URL}/fraud-analysis/analyze`,
  policyValidation: `${BASE_URL}/policy-analysis/validate`,
};

// Main test function
export default function () {
  // Health check
  group('Health Check', () => {
    const healthResponse = http.get(API_ENDPOINTS.healthCheck);
    check(healthResponse, {
      'health check status is 200': (r) => r.status === 200,
      'health check response time < 500ms': (r) => r.timings.duration < 500,
    });
  });

  // Primary claim processing workflow
  group('Claim Processing Workflow', () => {
    const claimData = generateClaimData();

    // Submit claim for processing
    const startTime = Date.now();

    const coordinateResponse = http.post(
      API_ENDPOINTS.coordinate,
      JSON.stringify(claimData),
      {
        headers: { 'Content-Type': 'application/json' },
        timeout: '30s',
      }
    );

    const processingTime = Date.now() - startTime;
    claimProcessingTime.add(processingTime);
    systemThroughput.add(1);

    const coordinateSuccess = check(coordinateResponse, {
      'claim coordination status is 200': (r) => r.status === 200,
      'claim coordination response time < 10s': (r) => r.timings.duration < 10000,
      'response contains human_routing': (r) => {
        try {
          const body = JSON.parse(r.body);
          return body.human_routing !== undefined;
        } catch {
          return false;
        }
      },
      'response contains ai_recommendation': (r) => {
        try {
          const body = JSON.parse(r.body);
          return body.ai_recommendation !== undefined;
        } catch {
          return false;
        }
      },
    });

    if (!coordinateSuccess) {
      errorRate.add(1);
    }

    // Extract task ID for human decision simulation
    let taskId = null;
    try {
      const responseBody = JSON.parse(coordinateResponse.body);
      taskId = responseBody.human_routing?.task_id;
    } catch (e) {
      console.error('Failed to parse coordinate response:', e);
    }

    // Simulate human decision (if task created)
    if (taskId) {
      sleep(1); // Simulate thinking time

      const humanDecision = {
        decision: Math.random() > 0.1 ? 'approve' : 'investigate', // 90% approval rate
        settlement_amount: claimData.claim_amount * (0.8 + Math.random() * 0.2),
        reasoning: 'Load test decision - claim appears valid based on AI analysis',
        reviewer_id: `TEST_REVIEWER_${Math.random().toString(36).substr(2, 5)}`,
        reviewer_license: generateUserCredentials().license,
      };

      const humanStartTime = Date.now();

      const humanResponse = http.post(
        `${API_ENDPOINTS.taskSubmit}/${taskId}`,
        JSON.stringify(humanDecision),
        {
          headers: { 'Content-Type': 'application/json' },
          timeout: '10s',
        }
      );

      const humanLatency = Date.now() - humanStartTime;
      humanWorkflowLatency.add(humanLatency);

      const humanSuccess = check(humanResponse, {
        'human decision status is 200': (r) => r.status === 200,
        'human decision response time < 2s': (r) => r.timings.duration < 2000,
        'human decision recorded': (r) => {
          try {
            const body = JSON.parse(r.body);
            return body.status === 'HUMAN_DECISION_RECORDED';
          } catch {
            return false;
          }
        },
      });

      if (!humanSuccess) {
        errorRate.add(1);
      }
    }
  });

  // Fraud analysis performance test
  group('Fraud Analysis Performance', () => {
    const claimData = generateClaimData();

    const fraudResponse = http.post(
      API_ENDPOINTS.fraudAnalysis,
      JSON.stringify(claimData),
      {
        headers: { 'Content-Type': 'application/json' },
        timeout: '15s',
      }
    );

    check(fraudResponse, {
      'fraud analysis status is 200': (r) => r.status === 200,
      'fraud analysis response time < 5s': (r) => r.timings.duration < 5000,
      'fraud score returned': (r) => {
        try {
          const body = JSON.parse(r.body);
          return body.fraud_analysis?.final_analysis?.fraud_score !== undefined;
        } catch {
          return false;
        }
      },
    });
  });

  // Policy validation performance test
  group('Policy Validation Performance', () => {
    const claimData = generateClaimData();

    const policyResponse = http.post(
      API_ENDPOINTS.policyValidation,
      JSON.stringify(claimData),
      {
        headers: { 'Content-Type': 'application/json' },
        timeout: '10s',
      }
    );

    check(policyResponse, {
      'policy validation status is 200': (r) => r.status === 200,
      'policy validation response time < 3s': (r) => r.timings.duration < 3000,
      'underwriter routing required': (r) => {
        try {
          const body = JSON.parse(r.body);
          return body.final_recommendation?.underwriter_required !== undefined;
        } catch {
          return false;
        }
      },
    });
  });

  // Simulate realistic user behavior
  sleep(Math.random() * 3 + 1); // 1-4 second pause between operations
}

// Setup function (runs once before test)
export function setup() {
  console.log('Starting load test...');
  console.log(`Base URL: ${BASE_URL}`);
  console.log(`Test scenarios: ${Object.keys(options.scenarios).join(', ')}`);

  // Verify system health before starting
  const healthCheck = http.get(API_ENDPOINTS.healthCheck);
  if (healthCheck.status !== 200) {
    throw new Error(`System health check failed: ${healthCheck.status}`);
  }

  return { startTime: Date.now() };
}

// Teardown function (runs once after test)
export function teardown(data) {
  const endTime = Date.now();
  const testDuration = (endTime - data.startTime) / 1000;
  console.log(`Test completed in ${testDuration} seconds`);
}

// Custom checks for business logic
export function handleSummary(data) {
  return {
    'stdout': textSummary(data, { indent: ' ', enableColors: true }),
    'summary.json': JSON.stringify(data, null, 2),
    'performance-report.html': htmlReport(data),
  };
}

function textSummary(data, options = {}) {
  const indent = options.indent || '';
  const enableColors = options.enableColors || false;

  let summary = `${indent}Load Test Summary\n`;
  summary += `${indent}================\n\n`;

  // Test duration
  const testDuration = data.state.testRunDurationMs / 1000;
  summary += `${indent}Test Duration: ${testDuration.toFixed(2)}s\n`;

  // HTTP metrics
  const httpReqs = data.metrics.http_reqs;
  const httpDuration = data.metrics.http_req_duration;
  const httpFailed = data.metrics.http_req_failed;

  summary += `${indent}Total Requests: ${httpReqs.values.count}\n`;
  summary += `${indent}Request Rate: ${(httpReqs.values.rate || 0).toFixed(2)}/s\n`;
  summary += `${indent}Request Duration (avg): ${(httpDuration.values.avg || 0).toFixed(2)}ms\n`;
  summary += `${indent}Request Duration (p95): ${(httpDuration.values['p(95)'] || 0).toFixed(2)}ms\n`;
  summary += `${indent}Failed Requests: ${((httpFailed.values.rate || 0) * 100).toFixed(2)}%\n\n`;

  // Custom metrics
  if (data.metrics.claim_processing_time) {
    const claimProcessing = data.metrics.claim_processing_time;
    summary += `${indent}Claim Processing Time (avg): ${(claimProcessing.values.avg || 0).toFixed(2)}ms\n`;
    summary += `${indent}Claim Processing Time (p95): ${(claimProcessing.values['p(95)'] || 0).toFixed(2)}ms\n`;
  }

  if (data.metrics.human_workflow_latency) {
    const workflowLatency = data.metrics.human_workflow_latency;
    summary += `${indent}Human Workflow Latency (avg): ${(workflowLatency.values.avg || 0).toFixed(2)}ms\n`;
    summary += `${indent}Human Workflow Latency (p90): ${(workflowLatency.values['p(90)'] || 0).toFixed(2)}ms\n`;
  }

  if (data.metrics.system_throughput) {
    const throughput = data.metrics.system_throughput;
    summary += `${indent}System Throughput: ${(throughput.values.rate || 0).toFixed(2)} claims/s\n`;
  }

  // Performance analysis
  summary += `\n${indent}Performance Analysis:\n`;

  const avgDuration = httpDuration.values.avg || 0;
  const p95Duration = httpDuration.values['p(95)'] || 0;
  const errorRate = (httpFailed.values.rate || 0) * 100;

  if (avgDuration < 1000) {
    summary += `${indent}✓ Average response time is excellent (${avgDuration.toFixed(2)}ms)\n`;
  } else if (avgDuration < 2000) {
    summary += `${indent}⚠ Average response time is acceptable (${avgDuration.toFixed(2)}ms)\n`;
  } else {
    summary += `${indent}✗ Average response time is poor (${avgDuration.toFixed(2)}ms)\n`;
  }

  if (p95Duration < 2000) {
    summary += `${indent}✓ 95th percentile response time is excellent (${p95Duration.toFixed(2)}ms)\n`;
  } else if (p95Duration < 5000) {
    summary += `${indent}⚠ 95th percentile response time is acceptable (${p95Duration.toFixed(2)}ms)\n`;
  } else {
    summary += `${indent}✗ 95th percentile response time is poor (${p95Duration.toFixed(2)}ms)\n`;
  }

  if (errorRate < 1) {
    summary += `${indent}✓ Error rate is excellent (${errorRate.toFixed(2)}%)\n`;
  } else if (errorRate < 5) {
    summary += `${indent}⚠ Error rate is acceptable (${errorRate.toFixed(2)}%)\n`;
  } else {
    summary += `${indent}✗ Error rate is poor (${errorRate.toFixed(2)}%)\n`;
  }

  return summary;
}

function htmlReport(data) {
  // Simplified HTML report generator
  return `
<!DOCTYPE html>
<html>
<head>
    <title>Load Test Performance Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .metric { margin: 10px 0; }
        .good { color: green; }
        .warning { color: orange; }
        .error { color: red; }
    </style>
</head>
<body>
    <h1>Insurance Claims Processing - Load Test Report</h1>
    <h2>Test Summary</h2>
    <div class="metric">Total Requests: ${data.metrics.http_reqs.values.count}</div>
    <div class="metric">Average Response Time: ${(data.metrics.http_req_duration.values.avg || 0).toFixed(2)}ms</div>
    <div class="metric">95th Percentile: ${(data.metrics.http_req_duration.values['p(95)'] || 0).toFixed(2)}ms</div>
    <div class="metric">Error Rate: ${((data.metrics.http_req_failed.values.rate || 0) * 100).toFixed(2)}%</div>

    <h2>Performance Assessment</h2>
    <p>System demonstrates ${
      (data.metrics.http_req_duration.values.avg || 0) < 2000 &&
      ((data.metrics.http_req_failed.values.rate || 0) * 100) < 5
        ? '<span class="good">EXCELLENT</span>'
        : '<span class="warning">ACCEPTABLE</span>'
    } performance under load.</p>

    <p>Generated at: ${new Date().toISOString()}</p>
</body>
</html>`;
}

export { textSummary };