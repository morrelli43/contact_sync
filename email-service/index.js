const express = require('express');
const nodemailer = require('nodemailer');
const cors = require('cors');
require('dotenv').config();

const app = express();
app.use(express.json());
app.use(cors());

// Health check endpoint
app.get('/health', (req, res) => {
    res.status(200).send('Email Service is running');
});

app.post('/send-it', async (req, res) => {
    const { first_name, surname, number, location, address_line_1, suburb, state, postcode, country,
            scooters = [], date_time, website_url } = req.body;

    // Spam Protection: Honeypot Check
    if (website_url) {
        console.log(`🚫 Spam detected: Honeypot field filled by connection from ${req.ip}`);
        // Return fake success to fool the bot
        return res.status(200).json({ success: true, message: 'Email sent successfully' });
    }

    // Create transporter using Mailu credentials from .env
    const transporter = nodemailer.createTransport({
        host: process.env.SMTP_HOST,
        port: process.env.SMTP_PORT || 587,
        secure: process.env.SMTP_SECURE === 'true', // true for 465, false for other ports
        auth: {
            user: process.env.SMTP_USER,
            pass: process.env.SMTP_PASS,
        },
    });

    const mailOptions = {
        from: `"${first_name} ${surname}" <${process.env.SMTP_FROM}>`,
        to: process.env.EMAIL_RECIPIENT || 'bookings@onyascoot.com',
        subject: `New Booking Enquiry - ${first_name} ${surname}`,
        text: (() => {
            const scooterLines = scooters.map(s => {
                const label = `${s.make || 'Unknown'} ${s.model || ''}`.trim() || 'Unknown Scooter';
                const issues = (s.issues || []).join(', ');
                const extra = s.issue_extra ? `\n  Extra: ${s.issue_extra}` : '';
                const photos = s.total_photos > 0 ? `\n  Photos: ${s.total_photos}` : '';
                return `Scooter ${s.scooter_num}: ${label}\n  Issues: ${issues}${extra}${photos}`;
            }).join('\n\n');
            return `New Booking Enquiry Received:\n\nDate: ${date_time || 'N/A'}\nName: ${first_name} ${surname}\nPhone: ${number}\nLocation: ${location || 'N/A'}\n\n${scooterLines}\n\n--\nOn Ya Scoot Booking System`;
        })(),
        html: (() => {
            const scooterRows = scooters.map(s => {
                const label = `${s.make || 'Unknown'} ${s.model || ''}`.trim() || 'Unknown Scooter';
                const issues = (s.issues || []).join(', ');
                const extra = s.issue_extra ? `<br><em>Extra: ${s.issue_extra}</em>` : '';
                const photos = s.total_photos > 0 ? `<br>Photos: ${s.total_photos}` : '';
                return `<tr><td style="padding:6px 12px;vertical-align:top"><strong>Scooter ${s.scooter_num}</strong></td><td style="padding:6px 12px">${label}<br>${issues}${extra}${photos}</td></tr>`;
            }).join('');
            return `
            <h3>New Booking Enquiry Received</h3>
            <p><strong>Date:</strong> ${date_time || 'N/A'}</p>
            <p><strong>Name:</strong> ${first_name} ${surname}</p>
            <p><strong>Phone:</strong> ${number}</p>
            <p><strong>Location:</strong> ${location || 'N/A'}</p>
            <table style="border-collapse:collapse;margin-top:12px">${scooterRows}</table>
            <br><hr><p><small>On Ya Scoot Booking System</small></p>`;
        })()
    };

    try {
        await transporter.sendMail(mailOptions);
        console.log(`✅ Email sent for ${first_name} ${surname}`);

        res.status(200).json({ success: true, message: 'Email sent successfully' });
    } catch (error) {
        console.error('❌ SMTP Error:', error);
        res.status(500).json({ success: false, message: 'Failed to send email', error: error.message });
    }
});

const PORT = process.env.PORT || 4311;
app.listen(PORT, () => {
    console.log(`Email service listening on port ${PORT}`);
});
