const express = require('express');
const axios = require('axios');
const cors = require('cors');
require('dotenv').config();

const app = express();
app.use(express.json());
app.use(cors());

// Health check endpoint
app.get('/health', (req, res) => {
    res.status(200).json({ status: 'ok', service: 'ops-forwarder', version: '1.0.1' });
});

/**
 * Accepted fields:
 *   first_name, surname, number, location,
 *   address_line_1, suburb, state, postcode, country,
 *   escooter_make, escooter_model, issue, issue_extra
 */
/**
 * Checks if a suburb has a callout fee set in the Operations site.
 * If not, fetches distance from googlemapsapi service and creates it.
 */
async function ensureCalloutFee(suburb) {
    if (!suburb) return;

    const opsBaseUrl = (process.env.OPS_WEBHOOK_URL || 'http://onya-operations-live-app:3000/api/webhooks/customer')
        .replace('/api/webhooks/customer', '');
    const calloutFeesUrl = `${opsBaseUrl}/api/callout-fees`;
    const googleMapsUrl = process.env.GOOGLE_MAPS_SERVICE_URL || 'http://googlemapsapi:4315';
    const googleMapsKey = process.env.GOOGLEMAPSAPI_SERVICE_API_KEY;

    const apiKey = process.env.OPS_API_KEY;
    const authHeaders = apiKey ? { 'Authorization': `Bearer ${apiKey}` } : {};

    try {
        // 1. Check if suburb already exists
        console.log(`[Ops-Forwarder] Checking callout fee for suburb: ${suburb}`);
        const { data: fees } = await axios.get(calloutFeesUrl, { headers: authHeaders });
        const exists = fees.some(f => f.suburb.toLowerCase() === suburb.toLowerCase());

        if (exists) {
            console.log(`[Ops-Forwarder] Callout fee already exists for ${suburb}`);
            return;
        }

        console.log(`[Ops-Forwarder] Callout fee missing for ${suburb}. Fetching travel data...`);

        // 2. Get distance/duration from googlemapsapi service
        const { data: searchData } = await axios.post(`${googleMapsUrl}/search`, {
            destination: suburb
        }, {
            headers: { 'x-api-key': googleMapsKey }
        });

        const dist = (searchData.distance.value / 1000).toFixed(2);
        const dur = Math.ceil(searchData.travelTime.value / 60);

        console.log(`[Ops-Forwarder] Creating callout fee for ${suburb}: ${dist}km, ${dur}mins`);

        // 3. Create callout fee on Operations site
        await axios.post(calloutFeesUrl, {
            suburb,
            distance: dist,
            duration: dur
        }, {
            headers: { 'Content-Type': 'application/json', ...authHeaders }
        });

        console.log(`✅ Successfully created callout fee for ${suburb}`);
    } catch (error) {
        console.error(`❌ Failed to ensure callout fee for ${suburb}:`, error.message);
        // We don't want to block the main form submission if this fails
    }
}

app.post('/send-it', async (req, res) => {
    const payload = req.body;

    console.log(`\n[Ops-Forwarder] Received submission: ${payload.first_name || ''} ${payload.surname || ''}`);

    // Ensure callout fee exists for the suburb
    if (payload.suburb) {
        // We don't await this to avoid delaying the response, 
        // but the user said "please make sure that is added", 
        // so maybe we SHOULD await it? 
        // The request says "make sure the callout price is ready for new form submissions".
        // If we await it, it ensures it's done before forwarding.
        await ensureCalloutFee(payload.suburb);
    }

    const targetUrl = process.env.OPS_WEBHOOK_URL || 'http://onya-operations-live-app:3000/api/webhooks/customer';

    // Forward recognised fields (deprecated top-level escooter_make/model/issue are excluded)
    const forwardPayload = {
        first_name: payload.first_name,
        surname: payload.surname,
        number: payload.number,
        ...(payload.date_time && { date_time: payload.date_time }),
        ...(payload.location && { location: payload.location }),
        ...(payload.address_line_1 && { address_line_1: payload.address_line_1 }),
        ...(payload.suburb && { suburb: payload.suburb }),
        ...(payload.state && { state: payload.state }),
        ...(payload.postcode && { postcode: payload.postcode }),
        ...(payload.country && { country: payload.country }),
        scooter_count: payload.scooter_count,
        has_photos: payload.has_photos,
        total_photos_all: payload.total_photos_all,
        scooters: payload.scooters,
    };

    const apiKey = process.env.OPS_API_KEY;
    const authHeaders = apiKey ? { 'Authorization': `Bearer ${apiKey}` } : {};

    try {
        console.log(`[Ops-Forwarder] Forwarding to ${targetUrl}`);
        const response = await axios.post(targetUrl, forwardPayload, {
            headers: { 'Content-Type': 'application/json', ...authHeaders },
            timeout: 10000, // 10 second timeout
        });

        if (response.status >= 200 && response.status < 300) {
            console.log('✅ Successfully forwarded to Operations site.');
            return res.status(200).json({ success: true, message: 'Forwarded to Operations site' });
        } else {
            console.error(`⚠️ Operations site returned status: ${response.status}`);
            return res.status(response.status).json({ success: false, message: 'Operations site error' });
        }
    } catch (error) {
        console.error('❌ Error forwarding to Operations site:', error.message);
        return res.status(500).json({
            success: false,
            message: 'Failed to forward to Operations site',
            error: error.message,
        });
    }
});

const PORT = process.env.PORT || 4313;
app.listen(PORT, () => {
    console.log(`Ops-Forwarder listening on port ${PORT}`);
    console.log(`Target Operations URL: ${process.env.OPS_WEBHOOK_URL || '(not set)'}`);
});
