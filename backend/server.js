require('dotenv').config();
const express = require('express');
const cors = require('cors');
const bodyParser = require('body-parser');
const fs = require('fs');
const path = require('path');
const { exec } = require('child_process');
const axios = require('axios');

const app = express();

/* IMPORTANT FOR RENDER */
const PORT = process.env.PORT || 5500;

/* ===================== MIDDLEWARE ===================== */

app.use(cors({
    origin: "*",
    methods: ["GET", "POST", "DELETE"],
    allowedHeaders: ["Content-Type", "Authorization"]
}));

app.use(bodyParser.json());

/* ===================== STATIC FRONTEND ===================== */

app.use(express.static(path.join(__dirname, 'frontend')));

/* ===================== DATA PATHS ===================== */

const dataDir = path.join(__dirname, 'data');

const ordersPath = path.join(dataDir, 'orders.json');
const feedbackPath = path.join(dataDir, 'feedback.json');
const summaryPath = path.join(dataDir, 'analytics_summary.json');
const weeklyPath = path.join(dataDir, 'weekly_insights.json');

const analyticsScript = path.join(__dirname, 'analytics.py');

/* ===================== INIT DATA FOLDER ===================== */

if (!fs.existsSync(dataDir)) {
    fs.mkdirSync(dataDir, { recursive: true });
}

/* ===================== FILE HELPERS ===================== */

function readJSON(filePath) {

    try {

        if (!fs.existsSync(filePath)) {
            fs.writeFileSync(filePath, JSON.stringify([], null, 2));
            return [];
        }

        const data = fs.readFileSync(filePath, 'utf8');
        return data ? JSON.parse(data) : [];

    } catch (err) {
        console.error("Read error:", err);
        return [];
    }

}

function writeJSON(filePath, data) {

    try {

        fs.writeFileSync(filePath, JSON.stringify(data, null, 2));
        return true;

    } catch (err) {

        console.error("Write error:", err);
        return false;

    }

}

/* ===================== ANALYTICS ===================== */

function runAnalytics() {

    if (!fs.existsSync(analyticsScript)) {
        console.log("Python analytics script not found");
        return;
    }

    exec(`python "${analyticsScript}"`, (error, stdout) => {

        if (error) {
            console.log("Python analytics failed");
        }

        if (stdout) {
            console.log(stdout);
        }

    });

}

/* ===================== ROUTES ===================== */

app.get('/api/health', (req, res) => {

    res.json({
        status: "OK",
        server: "SmartBite Restaurant",
        time: new Date().toISOString()
    });

});

/* ===================== ORDERS ===================== */

app.get('/api/orders', (req, res) => {

    res.json(readJSON(ordersPath));

});

app.post('/api/orders', (req, res) => {

    const orders = readJSON(ordersPath);

    const newOrder = req.body;

    newOrder.billNo = "SB" + Date.now();
    newOrder.date = new Date().toLocaleString();

    orders.push(newOrder);

    writeJSON(ordersPath, orders);

    runAnalytics();

    res.json({
        success: true,
        order: newOrder
    });

});

/* ===================== FEEDBACK ===================== */

app.get('/api/feedback', (req, res) => {

    res.json(readJSON(feedbackPath));

});

app.post('/api/feedback', (req, res) => {

    const feedback = readJSON(feedbackPath);

    const newFeedback = {
        id: "FB" + Date.now(),
        ...req.body,
        date: new Date().toLocaleString()
    };

    feedback.push(newFeedback);

    writeJSON(feedbackPath, feedback);

    runAnalytics();

    res.json({
        success: true,
        feedback: newFeedback
    });

});

/* ===================== ANALYTICS ===================== */

app.get('/api/analytics/summary', (req, res) => {

    if (fs.existsSync(summaryPath)) {

        res.json(JSON.parse(fs.readFileSync(summaryPath)));

    } else {

        res.json({
            message: "Analytics not ready"
        });

    }

});

app.get('/api/analytics/weekly', (req, res) => {

    if (fs.existsSync(weeklyPath)) {

        res.json(JSON.parse(fs.readFileSync(weeklyPath)));

    } else {

        res.json({
            message: "Weekly analytics not ready"
        });

    }

});

app.post('/api/analytics/run', (req, res) => {

    runAnalytics();

    res.json({
        success: true,
        message: "Analytics started"
    });

});

/* ===================== CHAT AI ===================== */

app.post('/api/chat', async (req, res) => {

    try {

        const userMessage = req.body.message;

        const response = await axios.post(
            "https://api.groq.com/openai/v1/chat/completions",
            {
                model: "llama-3.1-8b-instant",
                messages: [
                    {
                        role: "system",
                        content: "You are SmartBite Restaurant AI assistant."
                    },
                    {
                        role: "user",
                        content: userMessage
                    }
                ]
            },
            {
                headers: {
                    Authorization: `Bearer ${process.env.GROQ_API_KEY}`
                }
            }
        );

        res.json({
            reply: response.data.choices[0].message.content
        });

    } catch (err) {

        res.json({
            reply: "AI service unavailable"
        });

    }

});

/* ===================== MAIN PAGES ===================== */

app.get('/', (req, res) => {

    res.sendFile(path.join(__dirname, 'frontend/index.html'));

});

/* ===================== 404 ===================== */

app.use('/api/*', (req, res) => {

    res.status(404).json({
        error: "API endpoint not found"
    });

});

/* ===================== SERVER START ===================== */

app.listen(PORT, () => {

    console.log("=====================================");
    console.log("SMARTBITE RESTAURANT SERVER");
    console.log("Running on port:", PORT);
    console.log("=====================================");

});
