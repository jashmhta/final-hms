const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');
console.log('🚀 Running Comprehensive HMS Enterprise-Grade End-to-End Tests...');
const testPhases = [
    {
        name: 'Phase 1: User Journeys',
        script: 'npm run test:phase1',
        description: 'Patient Registration, Healthcare Provider, Administrator journeys',
        critical: true
    },
    {
        name: 'Phase 2: Clinical Workflows',
        script: 'npm run test:phase2',
        description: 'Outpatient, Inpatient, Emergency workflows',
        critical: true
    },
    {
        name: 'Phase 3: Administrative Workflows',
        script: 'npm run test:phase3',
        description: 'Billing, Pharmacy, Laboratory workflows',
        critical: true
    },
    {
        name: 'Phase 4: Integration Testing',
        script: 'npm run test:phase4',
        description: 'Frontend-Backend, Microservices, External integration',
        critical: true
    },
    {
        name: 'Phase 5: Data Flow Testing',
        script: 'npm run test:phase5',
        description: 'Patient, Clinical, Financial data flow',
        critical: true
    },
    {
        name: 'Phase 6: Performance Testing',
        script: 'npm run test:phase6',
        description: 'User Experience and System performance',
        critical: true
    },
    {
        name: 'Phase 7: Security Testing',
        script: 'npm run test:phase7',
        description: 'End-to-End security and compliance',
        critical: true
    },
    {
        name: 'Phase 8: Disaster Recovery',
        script: 'npm run test:phase8',
        description: 'Backup and recovery procedures',
        critical: true
    },
    {
        name: 'Phase 9: Accessibility Testing',
        script: 'npm run test:phase9',
        description: 'Mobile and accessibility compliance',
        critical: true
    }
];
const testResults = {
    startTime: new Date().toISOString(),
    phases: [],
    summary: {
        totalPhases: testPhases.length,
        passedPhases: 0,
        failedPhases: 0,
        skippedPhases: 0,
        totalTests: 0,
        passedTests: 0,
        failedTests: 0,
        skippedTests: 0
    },
    environment: {
        nodeVersion: process.version,
        platform: process.platform,
        arch: process.arch
    }
};
async function runTestPhase(phase) {
    console.log(`\n🔍 Running ${phase.name}...`);
    console.log(`📋 Description: ${phase.description}`);
    const phaseResult = {
        name: phase.name,
        description: phase.description,
        startTime: new Date().toISOString(),
        status: 'running',
        output: '',
        tests: {
            total: 0,
            passed: 0,
            failed: 0,
            skipped: 0
        }
    };
    try {
        const output = execSync(phase.script, {
            encoding: 'utf8',
            maxBuffer: 1024 * 1024 * 10, 
            timeout: 30 * 60 * 1000 
        });
        phaseResult.output = output;
        phaseResult.status = 'passed';
        phaseResult.endTime = new Date().toISOString();
        const testSummary = parseTestResults(output);
        phaseResult.tests = testSummary;
        testResults.summary.passedPhases++;
        testResults.summary.passedTests += testSummary.passed;
        testResults.summary.failedTests += testSummary.failed;
        testResults.summary.skippedTests += testSummary.skipped;
        testResults.summary.totalTests += testSummary.total;
        console.log(`✅ ${phase.name} completed successfully`);
        console.log(`📊 Tests: ${testSummary.passed} passed, ${testSummary.failed} failed, ${testSummary.skipped} skipped`);
    } catch (error) {
        phaseResult.status = 'failed';
        phaseResult.output = error.message;
        phaseResult.endTime = new Date().toISOString();
        phaseResult.error = error;
        testResults.summary.failedPhases++;
        console.log(`❌ ${phase.name} failed`);
        console.log(`🔥 Error: ${error.message}`);
        if (phase.critical) {
            console.log(`🚨 ${phase.name} is critical - stopping test execution`);
            throw error;
        }
    }
    testResults.phases.push(phaseResult);
    return phaseResult;
}
function parseTestResults(output) {
    const lines = output.split('\n');
    let tests = {
        total: 0,
        passed: 0,
        failed: 0,
        skipped: 0
    };
    lines.forEach(line => {
        const playwrightMatch = line.match(/(\d+)\s+failed.*(\d+)\s+passed.*(\d+)\s+skipped/);
        if (playwrightMatch) {
            tests.failed = parseInt(playwrightMatch[1]) || 0;
            tests.passed = parseInt(playwrightMatch[2]) || 0;
            tests.skipped = parseInt(playwrightMatch[3]) || 0;
            tests.total = tests.failed + tests.passed + tests.skipped;
        }
        const jestMatch = line.match(/Tests:\s+(\d+)\s+failed,\s+(\d+)\s+passed,\s+(\d+)\s+skipped/);
        if (jestMatch) {
            tests.failed = parseInt(jestMatch[1]) || 0;
            tests.passed = parseInt(jestMatch[2]) || 0;
            tests.skipped = parseInt(jestMatch[3]) || 0;
            tests.total = tests.failed + tests.passed + tests.skipped;
        }
        const totalMatch = line.match(/(\d+)\s+tests?/);
        if (totalMatch) {
            tests.total = Math.max(tests.total, parseInt(totalMatch[1]) || 0);
        }
    });
    return tests;
}
function generateTestReport() {
    testResults.endTime = new Date().toISOString();
    const report = {
        title: 'HMS Enterprise-Grade Comprehensive Test Report',
        generatedAt: new Date().toISOString(),
        results: testResults,
        summary: {
            overallStatus: testResults.summary.failedPhases === 0 ? 'PASSED' : 'FAILED',
            successRate: testResults.summary.totalTests > 0 ?
                ((testResults.summary.passedTests / testResults.summary.totalTests) * 100).toFixed(2) + '%' : '0%',
            duration: calculateDuration(testResults.startTime, testResults.endTime),
            recommendations: generateRecommendations()
        }
    };
    const reportPath = path.join('reports', 'comprehensive-test-report.json');
    fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));
    console.log(`📊 Detailed report saved to: ${reportPath}`);
    generateHtmlReport(report);
    return report;
}
function generateHtmlReport(report) {
    const html = `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HMS Enterprise-Grade Test Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header { text-align: center; margin-bottom: 30px; }
        .summary { background: #f8f9fa; padding: 20px; border-radius: 5px; margin-bottom: 20px; }
        .phase { border: 1px solid #ddd; margin: 10px 0; padding: 15px; border-radius: 5px; }
        .phase.passed { border-left: 5px solid #28a745; }
        .phase.failed { border-left: 5px solid #dc3545; }
        .phase.running { border-left: 5px solid #ffc107; }
        .status { padding: 5px 10px; border-radius: 3px; color: white; font-weight: bold; }
        .status.passed { background: #28a745; }
        .status.failed { background: #dc3545; }
        .status.running { background: #ffc107; color: black; }
        .metrics { display: flex; gap: 20px; margin: 10px 0; }
        .metric { background: #e9ecef; padding: 10px; border-radius: 5px; text-align: center; flex: 1; }
        .metric h4 { margin: 0; color: #495057; }
        .metric .value { font-size: 24px; font-weight: bold; color: #212529; }
        pre { background: #f8f9fa; padding: 15px; border-radius: 5px; overflow-x: auto; }
        .recommendations { background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 5px; margin: 20px 0; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>HMS Enterprise-Grade Test Report</h1>
            <p>Generated: ${new Date(report.generatedAt).toLocaleString()}</p>
            <div class="status ${report.summary.overallStatus.toLowerCase()}">${report.summary.overallStatus}</div>
        </div>
        <div class="summary">
            <h2>Test Summary</h2>
            <div class="metrics">
                <div class="metric">
                    <h4>Total Phases</h4>
                    <div class="value">${report.results.summary.totalPhases}</div>
                </div>
                <div class="metric">
                    <h4>Passed</h4>
                    <div class="value">${report.results.summary.passedPhases}</div>
                </div>
                <div class="metric">
                    <h4>Failed</h4>
                    <div class="value">${report.results.summary.failedPhases}</div>
                </div>
                <div class="metric">
                    <h4>Total Tests</h4>
                    <div class="value">${report.results.summary.totalTests}</div>
                </div>
                <div class="metric">
                    <h4>Success Rate</h4>
                    <div class="value">${report.summary.successRate}</div>
                </div>
                <div class="metric">
                    <h4>Duration</h4>
                    <div class="value">${report.summary.duration}</div>
                </div>
            </div>
        </div>
        <div class="recommendations">
            <h3>Recommendations</h3>
            <ul>
                ${report.summary.recommendations.map(rec => `<li>${rec}</li>`).join('')}
            </ul>
        </div>
        <h2>Phase Details</h2>
        ${report.results.phases.map(phase => `
            <div class="phase ${phase.status}">
                <h3>${phase.name}</h3>
                <p><strong>Description:</strong> ${phase.description}</p>
                <p><strong>Status:</strong> <span class="status ${phase.status}">${phase.status.toUpperCase()}</span></p>
                <p><strong>Duration:</strong> ${calculateDuration(phase.startTime, phase.endTime)}</p>
                <div class="metrics">
                    <div class="metric">
                        <h4>Total</h4>
                        <div class="value">${phase.tests.total}</div>
                    </div>
                    <div class="metric">
                        <h4>Passed</h4>
                        <div class="value">${phase.tests.passed}</div>
                    </div>
                    <div class="metric">
                        <h4>Failed</h4>
                        <div class="value">${phase.tests.failed}</div>
                    </div>
                    <div class="metric">
                        <h4>Skipped</h4>
                        <div class="value">${phase.tests.skipped}</div>
                    </div>
                </div>
                ${phase.error ? `<p><strong>Error:</strong> ${phase.error}</p>` : ''}
            </div>
        `).join('')}
        <h2>Environment</h2>
        <pre>${JSON.stringify(report.results.environment, null, 2)}</pre>
    </div>
</body>
</html>`;
    const htmlPath = path.join('reports', 'comprehensive-test-report.html');
    fs.writeFileSync(htmlPath, html);
    console.log(`🌐 HTML report saved to: ${htmlPath}`);
}
function calculateDuration(start, end) {
    const startTime = new Date(start);
    const endTime = new Date(end);
    const duration = endTime - startTime;
    const hours = Math.floor(duration / (1000 * 60 * 60));
    const minutes = Math.floor((duration % (1000 * 60 * 60)) / (1000 * 60));
    const seconds = Math.floor((duration % (1000 * 60)) / 1000);
    if (hours > 0) {
        return `${hours}h ${minutes}m ${seconds}s`;
    } else if (minutes > 0) {
        return `${minutes}m ${seconds}s`;
    } else {
        return `${seconds}s`;
    }
}
function generateRecommendations() {
    const recommendations = [];
    if (testResults.summary.failedPhases === 0) {
        recommendations.push('✅ All test phases passed - System is ready for deployment');
    } else {
        recommendations.push('❌ Failed test phases require immediate attention before deployment');
    }
    if (testResults.summary.failedTests > 0) {
        recommendations.push(`🔧 Fix ${testResults.summary.failedTests} failed tests to ensure system stability`);
    }
    if (testResults.summary.totalTests > 0) {
        const successRate = (testResults.summary.passedTests / testResults.summary.totalTests) * 100;
        if (successRate < 95) {
            recommendations.push('⚠️ Test success rate is below 95% - consider improving test coverage');
        }
    }
    recommendations.push('📊 Review detailed test reports for specific issues');
    recommendations.push('🔍 Conduct manual verification of critical business processes');
    recommendations.push('🚀 Schedule regular test runs to maintain system quality');
    return recommendations;
}
async function runComprehensiveTests() {
    console.log('🎯 Starting comprehensive end-to-end testing...');
    console.log('📋 Test Plan:');
    testPhases.forEach((phase, index) => {
        console.log(`${index + 1}. ${phase.name} - ${phase.description}`);
    });
    try {
        for (const phase of testPhases) {
            await runTestPhase(phase);
        }
        const report = generateTestReport();
        console.log('\n🎉 Comprehensive testing completed!');
        console.log('📊 Summary:');
        console.log(`   Total Phases: ${testResults.summary.totalPhases}`);
        console.log(`   Passed Phases: ${testResults.summary.passedPhases}`);
        console.log(`   Failed Phases: ${testResults.summary.failedPhases}`);
        console.log(`   Total Tests: ${testResults.summary.totalTests}`);
        console.log(`   Success Rate: ${report.summary.successRate}`);
        console.log(`   Duration: ${report.summary.duration}`);
        if (testResults.summary.failedPhases > 0) {
            console.log('\n❌ Some test phases failed - Please review the reports');
            process.exit(1);
        } else {
            console.log('\n✅ All test phases passed - System is ready!');
            process.exit(0);
        }
    } catch (error) {
        console.error('\n💥 Comprehensive testing failed:', error);
        process.exit(1);
    }
}
if (require.main === module) {
    runComprehensiveTests();
}
module.exports = { runComprehensiveTests, runTestPhase, generateTestReport };