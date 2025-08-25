Great — let’s summarize **what your "Vehicle Parking App - V1"** is all about in a clean, beginner-friendly way. This can be used in your report, presentation video, or README file:

---

### 🚗 **Vehicle Parking App - V1**

A Flask-based web application that helps manage and reserve 4-wheeler parking spots across multiple parking lots. It supports **Admin** and **User** roles with specific capabilities.

---

### ✅ **Key Features**

#### 👤 Admin (Superuser)

* No login or registration required — exists by default.
* Can **create, update, and delete** parking lots.
* Automatically generates parking spots based on capacity.
* Can view **status** (Occupied / Available) of every parking spot.
* Can see **user details** and **parking history**.
* Sees **summary charts** (e.g., total lots, occupied spots).

#### 🙋 User

* Can **register and login**.
* Can **book** a parking spot (auto-allotted).
* Can **release** the parking spot once the vehicle leaves.
* Sees **timestamps** (parking in/out) and **cost**.
* Views **personal parking history and summary charts**.

---

### 🧱 Technologies Used

| Layer      | Framework / Tools                            |
| ---------- | -------------------------------------------- |
| Backend    | Flask (Python)                               |
| Frontend   | HTML, CSS, Bootstrap, Jinja2                 |
| Database   | SQLite (programmatically created)            |
| Charts     | (Optional) Chart.js                          |
| Validation | HTML5/JavaScript (Frontend), Flask (Backend) |

---

### 🗂️ Data Models (Main Tables)

1. **User** – registered users
2. **Admin** – no table (hardcoded or auto-created on DB init)
3. **ParkingLot** – contains location, price, capacity
4. **ParkingSpot** – belongs to a lot, has status (A/O)
5. **Reservation** – connects user & spot, stores time and cost

---

### 🌐 Application Flow

1. **Admin logs in** → Adds Parking Lot → Spots auto-created
2. **User registers/logs in** → Selects lot → Gets a spot assigned
3. **User parks** → Status: "Occupied", Time starts
4. **User leaves** → Status: "Available", Time & Cost recorded
5. **Dashboards** → Show details, summaries, and charts

---

Would you like a visual wireframe, database ER diagram, or help in writing this into a proper README/report section?
