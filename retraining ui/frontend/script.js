const API_BASE = "http://127.0.0.1:8000";


const datasetInput =
    document.getElementById("datasetInput");

const fileName =
    document.getElementById("fileName");

const fileFormat =
    document.getElementById("fileFormat");

const fileStatus =
    document.getElementById("fileStatus");

const datasetStatus =
    document.getElementById("datasetStatus");

const startTrainingBtn =
    document.getElementById("startTrainingBtn");

const progressFill =
    document.getElementById("progressFill");

const progressPercentage =
    document.getElementById("progressPercentage");

const currentStage =
    document.getElementById("currentStage");

const elapsedTime =
    document.getElementById("elapsedTime");

const epochValue =
    document.getElementById("epochValue");

const epochTotal =
    document.getElementById("epochTotal");

const trainingLoss =
    document.getElementById("trainingLoss");

const validationLoss =
    document.getElementById("validationLoss");

const learningRate =
    document.getElementById("learningRate");

const pipelineState =
    document.getElementById("pipelineState");

const resultTime =
    document.getElementById("resultTime");

const resultEpoch =
    document.getElementById("resultEpoch");

const resultThreshold =
    document.getElementById("resultThreshold");

const resultAnomalies =
    document.getElementById("resultAnomalies");

const resultCustomers =
    document.getElementById("resultCustomers");

const resultCritical =
    document.getElementById("resultCritical");

const completionBadge =
    document.getElementById("completionBadge");

const recommendationTableBody =
    document.getElementById("recommendationTableBody");

const recommendationCount =
    document.getElementById("recommendationCount");


let uploadedDatasetPath = null;

let pollingInterval = null;


/* ==========================================
   FILE SELECTION
========================================== */

datasetInput.addEventListener(
    "change",
    () => {

        const file =
            datasetInput.files[0];

        if (!file) {

            fileName.textContent =
                "No file selected";

            fileFormat.textContent =
                "—";

            fileStatus.textContent =
                "Waiting";

            datasetStatus.textContent =
                "Not loaded";

            return;
        }

        fileName.textContent =
            file.name;

        const extension =
            file.name
                .split(".")
                .pop()
                .toUpperCase();

        fileFormat.textContent =
            extension;

        fileStatus.textContent =
            "Uploading...";

        datasetStatus.textContent =
            "Uploading";

        uploadDataset(file);
    }
);


/* ==========================================
   UPLOAD DATASET
========================================== */

async function uploadDataset(file) {

    try {

        const formData =
            new FormData();

        formData.append(
            "file",
            file
        );

        console.log("Uploading to:", `${API_BASE}/api/upload`);
        console.log("File:", file.name);

        const response =
            await fetch(
                `${API_BASE}/api/upload`,
                {
                    method: "POST",
                    body: formData
                }
            );

        const data =
            await response.json();

        if (!response.ok) {

            throw new Error(
                data.detail ||
                "Upload failed"
            );
        }

        uploadedDatasetPath =
            data.path;

        fileStatus.textContent =
            "Uploaded";

        datasetStatus.textContent =
            "Ready";

        startTrainingBtn.disabled =
            false;

    }

    catch (error) {

        console.error(error);

        fileStatus.textContent =
            "Failed";

        datasetStatus.textContent =
            "Upload failed";

        alert(
            "Dataset upload failed:\n\n" +
            error.message
        );
    }
}


/* ==========================================
   START TRAINING
========================================== */

startTrainingBtn.addEventListener(
    "click",
    async () => {

        if (!uploadedDatasetPath) {

            alert(
                "Please select a dataset first."
            );

            return;
        }

        try {

            startTrainingBtn.disabled =
                true;

            currentStage.textContent =
                "Starting training...";

            pipelineState.textContent =
                "Training in progress";

            completionBadge.textContent =
                "TRAINING";

            const response =
                await fetch(
                    `${API_BASE}/api/train?dataset_path=` +
                    encodeURIComponent(
                        uploadedDatasetPath
                    ),
                    {
                        method: "POST"
                    }
                );

            const data =
                await response.json();

            if (!response.ok) {

                throw new Error(
                    data.detail ||
                    "Training could not start"
                );
            }

            startPolling();

        }

        catch (error) {

            console.error(error);

            startTrainingBtn.disabled =
                false;

            alert(
                "Could not start training:\n\n" +
                error.message
            );
        }
    }
);


/* ==========================================
   POLL STATUS
========================================== */

function startPolling() {

    if (pollingInterval) {

        clearInterval(
            pollingInterval
        );
    }

    updateTrainingStatus();

    pollingInterval =
        setInterval(
            updateTrainingStatus,
            1000
        );
}


async function updateTrainingStatus() {

    try {

        const response =
            await fetch(
                `${API_BASE}/api/status`
            );

        const data =
            await response.json();

        updateUI(data);

        if (
            data.completed ||
            data.error
        ) {

            clearInterval(
                pollingInterval
            );

            pollingInterval =
                null;
        }

    }

    catch (error) {

        console.error(
            "Status error:",
            error
        );
    }
}


/* ==========================================
   UPDATE UI
========================================== */

function updateUI(data) {

    const progress =
        Number(data.progress || 0);

    progressFill.style.width =
        `${progress}%`;

    progressPercentage.textContent =
        `${progress}%`;

    currentStage.textContent =
        data.stage ||
        "Waiting...";

    pipelineState.textContent =
        data.stage ||
        "Waiting to start";


    /* ---------- Epoch ---------- */

    if (data.epoch) {

        epochValue.textContent =
            data.epoch;

        epochTotal.textContent =
            `of ${data.total_epochs}`;
    }


    /* ---------- Loss ---------- */

    if (data.training_loss !== null &&
        data.training_loss !== undefined) {

        trainingLoss.textContent =
            Number(
                data.training_loss
            ).toFixed(4);
    }


    if (data.validation_loss !== null &&
        data.validation_loss !== undefined) {

        validationLoss.textContent =
            Number(
                data.validation_loss
            ).toFixed(4);
    }


    /* ---------- Learning Rate ---------- */

    if (data.learning_rate !== null &&
        data.learning_rate !== undefined) {

        learningRate.textContent =
            Number(
                data.learning_rate
            ).toExponential(2);
    }


    /* ---------- Time ---------- */

    elapsedTime.textContent =
        formatTime(
            data.elapsed_seconds || 0
        );


    /* ---------- Results ---------- */

    if (data.threshold !== null &&
        data.threshold !== undefined) {

        resultThreshold.textContent =
            Number(
                data.threshold
            ).toFixed(4);
    }


    if (data.anomalies !== null &&
        data.anomalies !== undefined) {

        resultAnomalies.textContent =
            data.anomalies;
    }


    if (data.priority_customers !== null &&
        data.priority_customers !== undefined) {

        resultCustomers.textContent =
            data.priority_customers;
    }

    if (data.critical_customers !== null &&
    data.critical_customers !== undefined) {
        resultCritical.textContent =
            data.critical_customers;
    }


    /* ---------- Completion ---------- */

    if (data.completed) {

        completionBadge.textContent =
            "COMPLETED";

        resultTime.textContent =
            formatTime(
                data.elapsed_seconds || 0
            );

        resultEpoch.textContent =
            data.best_epoch ||
            data.epoch ||
            "—";

        startTrainingBtn.disabled =
            false;

        markCompleted();
        loadRecommendations();
    }


    /* ---------- Error ---------- */

    if (data.error) {

        completionBadge.textContent =
            "FAILED";

        pipelineState.textContent =
            "Training failed";

        currentStage.textContent =
            data.error;

        startTrainingBtn.disabled =
            false;
    }


    updatePipelineSteps(
        data.stage
    );
}


/* ==========================================
   PIPELINE VISUAL STATE
========================================== */

function updatePipelineSteps(stage) {

    const steps =
        document.querySelectorAll(
            ".pipeline-step"
        );

    const order = [
        "Data Loading",
        "Feature Engineering",
        "Data Preparation",
        "Autoencoder Training",
        "Anomaly Detection",
        "Risk Scoring",
        "Recommendations",
        "Business Simulation",
        "Completed"
    ];

    const currentIndex =
        order.indexOf(stage);

    steps.forEach(
        (step, index) => {

            const stepIndex =
                index;

            step.classList.remove(
                "active",
                "completed"
            );

            const status =
                step.querySelector(
                    ".step-status"
                );

            if (
                currentIndex > stepIndex
            ) {

                step.classList.add(
                    "completed"
                );

                status.textContent =
                    "COMPLETE";

            }
            else if (
                currentIndex === stepIndex
            ) {

                step.classList.add(
                    "active"
                );

                status.textContent =
                    "RUNNING";

            }
            else {

                status.textContent =
                    "WAITING";
            }
        }
    );
}


/* ==========================================
   COMPLETED STATE
========================================== */

function markCompleted() {

    document
        .querySelectorAll(
            ".pipeline-step"
        )
        .forEach(
            step => {

                step.classList.remove(
                    "active"
                );

                step.classList.add(
                    "completed"
                );

                step.querySelector(
                    ".step-status"
                ).textContent =
                    "COMPLETE";
            }
        );
}


/* ==========================================
   TIME FORMAT
========================================== */

function formatTime(seconds) {

    const minutes =
        Math.floor(
            seconds / 60
        );

    const remainingSeconds =
        seconds % 60;

    return (
        String(minutes)
            .padStart(2, "0")
        + ":" +
        String(
            remainingSeconds
        ).padStart(2, "0")
    );
}

/* ==========================================
   RECOMMENDATIONS
========================================== */

async function loadRecommendations() {

    recommendationTableBody.innerHTML = `
        <tr>
            <td colspan="7" class="table-empty">
                Loading recommendations...
            </td>
        </tr>
    `;

    try {

        const response =
            await fetch(
                `${API_BASE}/api/recommendations`
            );

        const data =
            await response.json();

        if (!response.ok) {

            throw new Error(
                data.detail ||
                "Could not load recommendations"
            );
        }

        const recommendations =
            Array.isArray(data.recommendations)
                ? data.recommendations
                : [];

        recommendationCount.textContent =
            `${recommendations.length} CUSTOMERS`;

        if (!recommendations.length) {

            recommendationTableBody.innerHTML = `
                <tr>
                    <td colspan="7" class="table-empty">
                        No recommendations available for this run.
                    </td>
                </tr>
            `;

            return;
        }

        recommendationTableBody.innerHTML =
            recommendations
                .map(createRecommendationRow)
                .join("");

    }
    catch (error) {

        console.error(
            "Recommendation error:",
            error
        );

        recommendationCount.textContent =
            "UNAVAILABLE";

        recommendationTableBody.innerHTML = `
            <tr>
                <td colspan="7" class="table-empty">
                    Recommendations could not be loaded.
                    Check that the FastAPI recommendation endpoint is running.
                </td>
            </tr>
        `;
    }
}


function createRecommendationRow(row) {

    const customer =
        escapeHtml(row["Customer ID"]);

    const riskScore =
        Number(row["Risk_Score"] ?? 0).toFixed(1);

    const riskCategory =
        escapeHtml(row["Risk_Category"] || "—");

    const potentialLoss =
        formatCurrency(row["Potential_Loss"]);

    const pattern =
        escapeHtml(
            row["Leakage_Pattern"] || "—"
        );

    const driver =
        escapeHtml(
            row["Primary_Driver"] || "—"
        );

    const recommendation =
        escapeHtml(
            row["Recommendation"] || "—"
        );

    const priority =
        escapeHtml(
            row["Recommendation_Priority"] || "MONITOR"
        );

    return `
        <tr>
            <td>
                <strong>${customer}</strong>
            </td>

            <td>
                <span class="risk-pill ${riskCategory.toLowerCase()}">
                    ${riskCategory}
                    <small>${riskScore}</small>
                </span>
            </td>

            <td>${potentialLoss}</td>

            <td>
                <span class="pattern-text">
                    ${pattern}
                </span>
            </td>

            <td>${driver}</td>

            <td class="recommendation-text">
                ${recommendation}
            </td>

            <td>
                <span class="priority-pill ${priority.toLowerCase()}">
                    ${priority}
                </span>
            </td>
        </tr>
    `;
}


function formatCurrency(value) {

    const number =
        Number(value);

    if (!Number.isFinite(number)) {
        return "—";
    }

    return new Intl.NumberFormat(
        "en-IN",
        {
            style: "currency",
            currency: "INR",
            maximumFractionDigits: 2
        }
    ).format(number);
}


function escapeHtml(value) {

    return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

/* ==========================================
   LOAD CUSTOMER RECOMMENDATIONS
========================================== */

async function loadRecommendations() {

    const recommendationBody =
    document.getElementById("recommendationTableBody");

    const recommendationBadge =
    document.getElementById("recommendationCount");

    if (!recommendationBody) {
        return;
    }

    try {

        recommendationBody.innerHTML = `
            <div class="recommendation-message">
                Loading recommendations...
            </div>
        `;

        const response = await fetch(
            `${API_BASE}/api/recommendations`
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.detail ||
                "Could not load recommendations"
            );
        }

        if (
            !data.recommendations ||
            data.recommendations.length === 0
        ) {
            recommendationBody.innerHTML = `
                <div class="recommendation-message">
                    No recommendations available.
                </div>
            `;

            if (recommendationBadge) {
                recommendationBadge.textContent =
                    "NO DATA";
            }

            return;
        }

        recommendationBody.innerHTML =
    data.recommendations.map(row => `
        <tr>
            <td>
                <strong>${row["Customer ID"]}</strong>
            </td>

            <td>
                <span class="risk-badge ${String(
                    row["Risk_Category"]
                ).toLowerCase()}">
                    ${row["Risk_Category"]}
                    ${Number(
                        row["Risk_Score"]
                    ).toFixed(1)}
                </span>
            </td>

            <td>
                ₹${Number(
                    row["Potential_Loss"]
                ).toLocaleString(
                    "en-IN",
                    {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2
                    }
                )}
            </td>

            <td>
                ${row["Leakage_Pattern"]}
            </td>

            <td>
                ${row["Primary_Driver"]}
            </td>

            <td>
                ${row["Recommendation"]}
            </td>

            <td>
                <span class="priority-badge">
                    ${row["Recommendation_Priority"]}
                </span>
            </td>
        </tr>
    `).join("");

        if (recommendationBadge) {
            recommendationBadge.textContent =
                `${data.count} RESULTS`;
        }

    }
    catch (error) {

        console.error(
            "Recommendation loading error:",
            error
        );

        recommendationBody.innerHTML = `
            <div class="recommendation-message">
                Recommendations could not be loaded.
                Check the FastAPI recommendation endpoint.
            </div>
        `;

        if (recommendationBadge) {
            recommendationBadge.textContent =
                "UNAVAILABLE";
        }
    }
}
loadRecommendations();