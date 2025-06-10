SplitZ - Deployed Application Access Guide

A production-ready expense-splitting web application with a modern UI, deployed on Render and backed by PostgreSQL.

## Live Application

Access the live application at:

> **[https://splitz-0zk8.onrender.com/](https://splitz-0zk8.onrender.com/)**

All application components and the database are hosted and managed on Render.

## Features

* 💰 **Expense Tracking**: Easily add, edit, and delete shared expenses with customizable categories.
* 👥 **Automatic Person Management**: Participants are created automatically when adding expenses.
* ⚖️ **Balance Overview**: Instantly view who owes money and who should receive funds.
* 🔄 **Optimized Settlements**: Smart algorithm to minimize the number of transactions for settling balances.
* 📱 **Responsive Design**: Fully responsive layout for desktop, tablet, and mobile devices.
* 🎨 **Modern UI**: Clean light theme with smooth animations and Bootstrap 5 styling.

## Hosted Database

The PostgreSQL database is provisioned and maintained on Render. You can connect using the following credentials:

```txt
postgresql://kshiitij:qvidooZgRgYbFyxLeml29ppPom48iMKf@dpg-d13vlg6mcj7s738ghum0-a/kshitij_69yp
```

> **Note:** Treat these credentials as sensitive. Rotate or revoke them if compromised.

## Usage Instructions

1. **Navigate to the App**: Open the URL in your browser: `https://splitz-0zk8.onrender.com/`.
2. **Add an Expense**: Click **Add Expense**, enter details (amount, description, participants) and submit.
3. **View Balances**: Go to **Balances** to see each person's net position.
4. **Settle Up**: Click **Settlements** for recommended transactions to zero out balances.
5. **Manage Entries**: Use **Edit** or **Delete** actions on any expense record.

## Security & Environment

* The application enforces HTTPS in production.
* Secret keys and sensitive configuration are managed via Render's Environment Settings.
* Application logs and performance metrics are accessible through the Render dashboard.

## Support & Maintenance

For issues or enhancement requests, create an issue in the [SplitZ GitHub repository](https://github.com/your-org/splitz).

## License

This project is open-source under the MIT License.
