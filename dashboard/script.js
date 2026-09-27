console.log("Profit Leakage Dashboard loaded successfully!");


// ============================================
// 1. LOAD DASHBOARD DATA
// ============================================

fetch("../dashboard_data.csv")
    .then(response => {

        if (!response.ok) {
            throw new Error("Could not load dashboard_data.csv");
        }

        return response.text();
    })

    .then(csvData => {

        console.log("dashboard_data.csv loaded successfully!");

        // Convert CSV into rows
        const rows = parseCSV(csvData);

        console.log("Total CSV rows:", rows.length);

        if (rows.length === 0) {
            throw new Error("CSV file is empty");
        }

        // First row contains column names
        const headers = rows[0];

        // Convert remaining rows into objects
        const data = rows.slice(1).map(row => {

            let obj = {};

            headers.forEach((header, index) => {
                obj[header] = row[index] || "";
            });

            return obj;
        });

        console.log("Dashboard records loaded:", data.length);

        // Start updating dashboard
        updateDashboard(data);

    })

    .catch(error => {

        console.error(
            "Error loading dashboard data:",
            error
        );

    });


// ============================================
// 2. CSV PARSER
// ============================================

function parseCSV(text) {

    const rows = [];
    let row = [];
    let value = "";
    let insideQuotes = false;

    for (let i = 0; i < text.length; i++) {

        const character = text[i];
        const nextCharacter = text[i + 1];

        // Handle quotes
        if (character === '"' && insideQuotes && nextCharacter === '"') {

            value += '"';
            i++;

        }

        else if (character === '"') {

            insideQuotes = !insideQuotes;

        }

        // New column
        else if (character === "," && !insideQuotes) {

            row.push(value.trim());
            value = "";

        }

        // New row
        else if (
            (character === "\n" || character === "\r")
            && !insideQuotes
        ) {

            if (value !== "" || row.length > 0) {

                row.push(value.trim());

                rows.push(row);

                row = [];
                value = "";
            }

        }

        else {

            value += character;

        }
    }

    // Add final value
    if (value !== "" || row.length > 0) {

        row.push(value.trim());
        rows.push(row);

    }

    return rows;
}


// ============================================
// 3. UPDATE DASHBOARD
// ============================================

function updateDashboard(data) {

    console.log("Updating dashboard...");

    // ----------------------------------------
    // Unique customers
    // ----------------------------------------

    const customers = new Set(
        data.map(row => row["Customer ID"])
    );

    const customersAnalyzed = customers.size;


    // ----------------------------------------
    // Critical customers
    // ----------------------------------------

    const criticalCustomers = data.filter(
        row => row["Risk_Category"] === "CRITICAL"
    ).length;


    // ----------------------------------------
    // Potential loss
    // ----------------------------------------

    const potentialLoss = data.reduce(
        (total, row) =>
            total + Number(row["Potential_Loss"] || 0),
        0
    );


    // ----------------------------------------
    // Target customer sales
    // ----------------------------------------

    const targetCustomerSales = data.reduce(
        (total, row) =>
            total + Number(row["Total_Sales"] || 0),
        0
    );


    console.log("Customers:", customersAnalyzed);
    console.log("Critical customers:", criticalCustomers);
    console.log("Potential loss:", potentialLoss);
    console.log("Target sales:", targetCustomerSales);


    // ========================================
    // 4. PUT VALUES INTO KPI CARDS
    // ========================================

    const placeholders = document.querySelectorAll(
        "body *"
    );

    const kpiValues = [

        customersAnalyzed.toLocaleString(),

        criticalCustomers.toLocaleString(),

        "₹" + potentialLoss.toLocaleString(
            "en-IN",
            {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
            }
        ),

        "₹" + targetCustomerSales.toLocaleString(
            "en-IN",
            {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
            }
        )

    ];


    // Find the first four "--" elements
    let replaced = 0;

    placeholders.forEach(element => {

        if (
            replaced < 4 &&
            element.textContent.trim() === "--"
        ) {

            element.textContent =
                kpiValues[replaced];

            replaced++;

        }

    });


    console.log(
        "KPI cards updated:",
        replaced
    );
    createRiskChart(data);
    createLeakageChart(data);
    createRecommendationTable(data);
    loadImpactData();

}

// ============================================
// 5. RISK DISTRIBUTION CHART
// ============================================

function createRiskChart(data) {

    const riskCounts = {
        CRITICAL: 0,
        HIGH: 0,
        MEDIUM: 0,
        LOW: 0
    };

    // Count customers in each risk category
    data.forEach(row => {

        const risk = row["Risk_Category"];

        if (riskCounts.hasOwnProperty(risk)) {
            riskCounts[risk]++;
        }

    });

    console.log("Risk distribution:", riskCounts);


    // Find the canvas
    const canvas = document.getElementById("riskChart");

    if (!canvas) {
        console.error("riskChart canvas not found!");
        return;
    }


    // Destroy previous chart if one already exists
    if (window.riskChartInstance) {
        window.riskChartInstance.destroy();
    }


    // Create chart
    window.riskChartInstance = new Chart(canvas, {

        type: "bar",

        data: {

            labels: [
                "CRITICAL",
                "HIGH",
                "MEDIUM",
                "LOW"
            ],

            datasets: [{

                label: "Customers",

                data: [
                    riskCounts.CRITICAL,
                    riskCounts.HIGH,
                    riskCounts.MEDIUM,
                    riskCounts.LOW
                ],

                backgroundColor: [
                    "#dc2626",
                    "#f97316",
                    "#facc15",
                    "#22c55e"
                ],

                borderRadius: 8,

                borderSkipped: false,

                barThickness: 38

            }]

        },


        options: {

            indexAxis: "y",

            responsive: true,

            maintainAspectRatio: false,


            plugins: {

                legend: {
                    display: false
                },

                title: {
                    display: true,

                    text: "Customer Risk Distribution",

                    font: {
                        size: 18,
                        weight: "bold"
                    },

                    padding: {
                        bottom: 20
                    }
                },

                tooltip: {

                    callbacks: {

                        label: function(context) {

                            return " Customers: " + context.raw;

                        }

                    }

                }

            },


            scales: {

                x: {

                    beginAtZero: true,

                    ticks: {
                        precision: 0
                    },

                    title: {

                        display: true,

                        text: "Number of Customers"

                    }

                },


                y: {

                    title: {

                        display: true,

                        text: "Risk Category"

                    }

                }

            }

        }

    });

}

// ============================================
// 6. PROFIT LEAKAGE PATTERN CHART
// ============================================

function createLeakageChart(data) {

    const patternCounts = {
        GENERAL_PROFITABILITY: 0,
        MULTI_FACTOR: 0,
        SHIPPING_DRIVEN: 0,
        DISCOUNT_DRIVEN: 0,
        MARGIN_DRIVEN: 0
    };


    // Count each leakage pattern
    data.forEach(row => {

        const pattern = row["Leakage_Pattern"];

        if (patternCounts.hasOwnProperty(pattern)) {
            patternCounts[pattern]++;
        }

    });


    console.log(
        "Leakage pattern distribution:",
        patternCounts
    );


    // Find canvas
    const canvas = document.getElementById("leakageChart");

    if (!canvas) {

        console.error(
            "leakageChart canvas not found!"
        );

        return;
    }


    // Destroy previous chart if it exists
    if (window.leakageChartInstance) {

        window.leakageChartInstance.destroy();

    }


    // Create chart
    window.leakageChartInstance = new Chart(
        canvas,
        {

            type: "bar",

            data: {

                labels: [
                    "GENERAL PROFITABILITY",
                    "MULTI FACTOR",
                    "SHIPPING DRIVEN",
                    "DISCOUNT DRIVEN",
                    "MARGIN DRIVEN"
                ],

                datasets: [{

                    label: "Customers",

                    data: [

                        patternCounts.GENERAL_PROFITABILITY,

                        patternCounts.MULTI_FACTOR,

                        patternCounts.SHIPPING_DRIVEN,

                        patternCounts.DISCOUNT_DRIVEN,

                        patternCounts.MARGIN_DRIVEN

                    ],

                    backgroundColor: [
                        "#2563eb",
                        "#7c3aed",
                        "#f97316",
                        "#eab308",
                        "#16a34a"
                    ],

                    borderRadius: 8,

                    borderSkipped: false,

                    barThickness: 35

                }]

            },


            options: {

                indexAxis: "y",

                responsive: true,

                maintainAspectRatio: false,


                plugins: {

                    legend: {
                        display: false
                    },

                    title: {

                        display: true,

                        text: "Profit Leakage Pattern Distribution",

                        font: {
                            size: 18,
                            weight: "bold"
                        },

                        padding: {
                            bottom: 20
                        }

                    },

                    tooltip: {

                        callbacks: {

                            label: function(context) {

                                return (
                                    " Customers: "
                                    + context.raw
                                );

                            }

                        }

                    }

                },


                scales: {

                    x: {

                        beginAtZero: true,

                        ticks: {
                            precision: 0
                        },

                        title: {

                            display: true,

                            text: "Number of Customers"

                        }

                    },


                    y: {

                        title: {

                            display: true,

                            text: "Leakage Pattern"

                        }

                    }

                }

            }

        }
    );

}

// ============================================
// 7. PRIORITY CUSTOMER RECOMMENDATIONS
// ============================================

function createRecommendationTable(data) {

    console.log("Creating recommendation table...");

    const tableBody = document.getElementById(
        "recommendationTableBody"
    );

    if (!tableBody) {

        console.error(
            "Recommendation table body not found!"
        );

        return;
    }


    // Sort customers by risk score
    const sortedData = [...data].sort(
        (a, b) =>
            Number(b["Risk_Score"] || 0)
            -
            Number(a["Risk_Score"] || 0)
    );


    // Show top 20
    const topCustomers = sortedData.slice(0, 20);


    // Clear existing rows
    tableBody.innerHTML = "";


    // Create table rows
    topCustomers.forEach(row => {

        const tableRow = document.createElement("tr");


        // ----------------------------------------
        // Risk category
        // ----------------------------------------

        const riskCategory =
            row["Risk_Category"] || "UNKNOWN";

        const riskClass =
            "risk-" +
            riskCategory.toLowerCase();


        // ----------------------------------------
        // Priority
        // ----------------------------------------

        const priority =
            row["Recommendation_Priority"] || "NORMAL";

        let priorityClass = "priority-normal";

        if (priority === "IMMEDIATE") {

            priorityClass = "priority-immediate";

        }

        else if (priority === "HIGH") {

            priorityClass = "priority-high";

        }


        // ----------------------------------------
        // Leakage pattern
        // ----------------------------------------

        const pattern =
            (row["Leakage_Pattern"] || "")
            .replaceAll("_", " ");


        // ----------------------------------------
        // Potential loss
        // ----------------------------------------

        const potentialLoss =
            Number(row["Potential_Loss"] || 0);


        // ----------------------------------------
        // Recommendation
        // ----------------------------------------

        const recommendation =
            row["Recommendation"] || "No recommendation";


        // ----------------------------------------
        // Build row
        // ----------------------------------------

        tableRow.innerHTML = `

            <td>
                <span class="customer-id">
                    ${row["Customer ID"] || ""}
                </span>
            </td>

            <td>
                <span class="risk-score">
                    ${Number(row["Risk_Score"] || 0).toFixed(1)}
                </span>
            </td>

            <td>
                <span class="${riskClass}">
                    ${riskCategory}
                </span>
            </td>

            <td>
                ₹${potentialLoss.toLocaleString(
                    "en-IN",
                    {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2
                    }
                )}
            </td>

            <td>
                <span class="leakage-pattern">
                    ${pattern}
                </span>
            </td>

            <td>
                <div class="recommendation-text">
                    ${recommendation}
                </div>
            </td>

            <td>
                <span class="${priorityClass}">
                    ${priority}
                </span>
            </td>

        `;


        tableBody.appendChild(tableRow);

    });


    // Update table description
    const countElement =
        document.getElementById(
            "recommendationCount"
        );

    if (countElement) {

        countElement.textContent =
            `Showing top ${topCustomers.length} customers by risk score`;

    }


    console.log(
        "Recommendation table created:",
        topCustomers.length,
        "customers"
    );

}

// ============================================
// 8. SIX-MONTH BUSINESS IMPACT
// ============================================

function loadImpactData() {

    fetch("../simulation_results.csv")

        .then(response => {

            if (!response.ok) {
                throw new Error(
                    "Could not load simulation_results.csv"
                );
            }

            return response.text();

        })

        .then(csvData => {

            console.log(
                "simulation_results.csv loaded successfully!"
            );

            const rows = parseCSV(csvData);

            console.log(
                "Simulation rows:",
                rows.length
            );

            if (rows.length === 0) {
                throw new Error(
                    "Simulation CSV is empty"
                );
            }

            const headers = rows[0];

            const data = rows.slice(1).map(row => {

                let obj = {};

                headers.forEach((header, index) => {

                    obj[header] =
                        row[index] || "";

                });

                return obj;

            });

            console.log(
                "Simulation records loaded:",
                data.length
            );

            createImpactChart(data);

        })

        .catch(error => {

            console.error(
                "Error loading simulation data:",
                error
            );

        });

}


// ============================================
// CREATE IMPACT CHART
// ============================================

function createImpactChart(data) {

    const canvas =
        document.getElementById("impactChart");

    if (!canvas) {

        console.error(
            "impactChart canvas not found!"
        );

        return;

    }


    // Keep only one record per
    // scenario + month
    const scenarios = {

        Conservative: [],
        Moderate: [],
        Aggressive: []

    };


    data.forEach(row => {

        const scenario =
            row["Scenario"];

        if (
            scenarios.hasOwnProperty(scenario)
        ) {

            scenarios[scenario].push(row);

        }

    });


    // Sort each scenario by month
    Object.keys(scenarios).forEach(
        scenario => {

            scenarios[scenario].sort(
                (a, b) =>
                    Number(a["Month"]) -
                    Number(b["Month"])
            );

        }
    );


    console.log(
        "Impact scenarios:",
        scenarios
    );


    // ----------------------------------------
    // Destroy previous chart
    // ----------------------------------------

    if (window.impactChartInstance) {

        window.impactChartInstance.destroy();

    }


    // ----------------------------------------
    // Create chart
    // ----------------------------------------

    window.impactChartInstance =
        new Chart(
            canvas,
            {

                type: "line",

                data: {

                    labels: [
                        "Month 1",
                        "Month 2",
                        "Month 3",
                        "Month 4",
                        "Month 5",
                        "Month 6"
                    ],

                    datasets: [

                        {
                            label: "Conservative",

                            data:
                                scenarios
                                    .Conservative
                                    .map(
                                        row =>
                                            Number(
                                                row[
                                                    "Cumulative_Business_Impact"
                                                ]
                                            )
                                    ),

                            borderColor: "#2563eb",

                            backgroundColor:
                                "rgba(37, 99, 235, 0.10)",

                            borderWidth: 3,

                            tension: 0.3,

                            fill: false,

                            pointRadius: 5

                        },


                        {
                            label: "Moderate",

                            data:
                                scenarios
                                    .Moderate
                                    .map(
                                        row =>
                                            Number(
                                                row[
                                                    "Cumulative_Business_Impact"
                                                ]
                                            )
                                    ),

                            borderColor: "#16a34a",

                            backgroundColor:
                                "rgba(22, 163, 74, 0.10)",

                            borderWidth: 4,

                            tension: 0.3,

                            fill: false,

                            pointRadius: 5

                        },


                        {
                            label: "Aggressive",

                            data:
                                scenarios
                                    .Aggressive
                                    .map(
                                        row =>
                                            Number(
                                                row[
                                                    "Cumulative_Business_Impact"
                                                ]
                                            )
                                    ),

                            borderColor: "#dc2626",

                            backgroundColor:
                                "rgba(220, 38, 38, 0.10)",

                            borderWidth: 3,

                            tension: 0.3,

                            fill: false,

                            pointRadius: 5

                        }

                    ]

                },


                options: {

                    responsive: true,

                    maintainAspectRatio: false,


                    plugins: {

                        title: {

                            display: true,

                            text:
                                "Projected Cumulative Business Impact",

                            font: {

                                size: 18,

                                weight: "bold"

                            },

                            padding: {

                                bottom: 20

                            }

                        },

                        legend: {

                            display: true,

                            position: "top"

                        },

                        tooltip: {

                            callbacks: {

                                label:
                                    function(context) {

                                        return (
                                            context.dataset.label
                                            + ": ₹"
                                            + Number(
                                                context.raw
                                            ).toLocaleString(
                                                "en-IN",
                                                {
                                                    minimumFractionDigits: 0,
                                                    maximumFractionDigits: 0
                                                }
                                            )
                                        );

                                    }

                            }

                        }

                    },


                    scales: {

                        x: {

                            title: {

                                display: true,

                                text: "Month"

                            }

                        },

                        y: {

                            beginAtZero: true,

                            title: {

                                display: true,

                                text:
                                    "Cumulative Business Impact (₹)"

                            },

                            ticks: {

                                callback:
                                    function(value) {

                                        return "₹" +
                                            Number(value)
                                                .toLocaleString(
                                                    "en-IN"
                                                );

                                    }

                            }

                        }

                    }

                }

            }
        );

}