# Complete Implementation Guide
## My Content Generator Rebrand & Credit System Overhaul

This document outlines all changes needed to complete the system transformation.

---

## ✅ COMPLETED

### Phase 1: Tiered Credit System (DONE)
- ✅ Updated `credit_system.py` with tiered pricing
- ✅ Changed from dollar-based to credit-based system
- ✅ Implemented `calculate_credits_from_purchase()` function
- ✅ Created `CREDIT_PACKAGES` array with 7 tiers
- ✅ Committed to Git (commit 9c86335)

---

## 🔄 REMAINING TASKS

### Phase 2: Dashboard UI Updates

**File: `static/dashboard.html`**

#### A. Update Credit Packages Display (Lines 688-697)
Replace current packages with new tiered packages:

```html
<select id="creditPackage" style="font-size: 1.1em; padding: 16px;">
    <option value="10">$10 - Starter (5 articles @ $1.99 each)</option>
    <option value="25" selected>$25 - Basic (12 articles @ $1.99 each)</option>
    <option value="50">$50 - Plus (25 articles @ $1.99 each)</option>
    <option value="100">$100 - Pro (57 articles @ $1.75 each)</option>
    <option value="250">$250 - Business (166 articles @ $1.50 each)</option>
    <option value="500">$500 - Premium (400 articles @ $1.25 each)</option>
    <option value="1000">$1000 - Enterprise (1010 articles @ $0.99 each)</option>
</select>
```

#### B. Update Credit Balance Display (Lines 572-576, 705-710)
Change from "$X.XX" to "X credits":

```html
<!-- Stats card -->
<div class="stat-number"><span id="creditBalance">0</span> credits</div>

<!-- Billing tab balance display -->
<p style="font-size: 2em; font-weight: 700; color: #ff6b11; margin: 10px 0;">
    <span id="currentBalance">0</span> credits
</p>
<p style="color: #666; font-size: 0.9em;">
    Available articles: <strong id="estimatedArticles">0</strong>
</p>
```

#### C. Update JavaScript Credit Loading (Lines 1165-1172)
```javascript
function loadCredits() {
    fetch('/api/profile', {
        credentials: 'include'
    })
    .then(res => res.json())
    .then(data => {
        const credits = Math.floor(data.credit_balance || 0);  // Convert to int

        document.getElementById('creditBalance').textContent = credits;
        document.getElementById('currentBalance').textContent = credits;
        document.getElementById('estimatedArticles').textContent = credits;  // 1:1 ratio
    })
    .catch(err => console.error('Error loading credits:', err));
}
```

#### D. Update Transaction History Display (Lines 1198-1204)
```javascript
data.transactions.forEach(t => {
    const date = new Date(t.created_at).toLocaleDateString();
    const isPurchase = t.transaction_type === 'purchase' || t.transaction_type === 'welcome';
    const type = isPurchase ? '💳 Purchase' : '📝 Article';
    const amountClass = isPurchase ? 'color: #28a745' : 'color: #dc3545';
    const amount = isPurchase ? `+${t.amount} credits` : `-${Math.abs(t.amount)} credit`;

    html += `<tr style="border-bottom: 1px solid #eee;"><td style="padding: 12px;">${date}</td><td style="padding: 12px;">${type}</td><td style="padding: 12px; text-align: right; ${amountClass}; font-weight: 600;">${amount}</td></tr>`;
});
```

---

### Phase 3: Rebranding to "My Content Generator"

#### A. Update Dashboard Header (dashboard.html line 541-544)
```html
<div class="header">
    <img src="/static/MY_CONTENT_GEN WEBLOGO.png" alt="My Content Generator Logo" class="header-logo">
    <div class="header-text">
        <h1>My Content Generator</h1>
        <p>AI-Powered Blog Content for WordPress</p>
    </div>
</div>
```

#### B. Update Page Title (dashboard.html line 6)
```html
<title>My Content Generator - Dashboard</title>
```

#### C. Update Favicon (dashboard.html line 7)
```html
<link rel="icon" type="image/png" href="/static/MY_CONTENT_GEN.png">
```

#### D. Update Landing Page (if exists)
Search and replace all instances:
- "EZWAI SMM" → "My Content Generator"
- "EZWai logo  and Tagline.png" → "MY_CONTENT_GEN WEBLOGO.png"
- "ezwai icon portal copy.webp" → "MY_CONTENT_GEN.png"

---

### Phase 4: Update Brand Colors

**File: `static/dashboard.html`**

#### A. Primary Brand Colors (Lines 19, 144-145, 184, 225, 349-361, 390)

**Old Colors:**
- Teal: `#08b0c4`, `#08b2c6`, `#06899a`
- Orange: `#ff6b11`, `#e55a00`

**New Colors:**
- Purple/Violet: `#6B5DD3`
- Blue: `#4A9FE8`
- Orange/Coral: `#FF6B4A`
- Dark Navy: `#2C3E50`

**Changes Needed:**

```css
body {
    background: linear-gradient(135deg, #6B5DD3 0%, #4A9FE8 100%);
}

.btn {
    background: linear-gradient(135deg, #FF6B4A 0%, #e55a00 100%);
}

.stat-card {
    background: linear-gradient(135deg, #4A9FE8 0%, #6B5DD3 100%);
}

.stat-card.credits {
    background: linear-gradient(135deg, #FF6B4A 0%, #e55a00 100%);
}

.tab-btn.active {
    background: linear-gradient(135deg, #FF6B4A 0%, #e55a00 100%);
}

input:checked + .toggle-slider {
    background-color: #4A9FE8;
}
```

#### B. Update Default Brand Colors in Database

**File: `app_v3.py`** (User model lines ~145-147)

```python
brand_primary_color = db.Column(db.String(7), default='#6B5DD3')  # Purple
brand_accent_color = db.Column(db.String(7), default='#FF6B4A')  # Coral/Orange
```

---

### Phase 5: Add Profile Dropdown Menu

**File: `static/dashboard.html`**

#### A. Add Profile Dropdown HTML (After line 544, inside header)

```html
<div class="profile-menu-container">
    <div class="profile-trigger" onclick="toggleProfileMenu()">
        <img id="profileImage" src="/static/default-avatar.png" alt="Profile" class="profile-avatar">
        <span id="profileName">User</span>
        <svg width="12" height="8" viewBox="0 0 12 8" fill="currentColor">
            <path d="M1 1l5 5 5-5"/>
        </svg>
    </div>
    <div id="profileDropdown" class="profile-dropdown" style="display: none;">
        <a href="#" onclick="openManageProfile(); return false;">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                <path d="M8 8a3 3 0 100-6 3 3 0 000 6zm0 2c-2.7 0-8 1.3-8 4v2h16v-2c0-2.7-5.3-4-8-4z"/>
            </svg>
            Manage Profile
        </a>
        <a href="#" onclick="handleLogout(); return false;">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                <path d="M3 0v1H0v2h3v13h10V3h3V1h-3V0H3zm2 3h6v11H5V3z"/>
            </svg>
            Log Out
        </a>
    </div>
</div>
```

#### B. Add Profile Dropdown CSS (In <style> section)

```css
.profile-menu-container {
    position: relative;
    margin-left: auto;
}

.profile-trigger {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 8px 16px;
    border-radius: 25px;
    background: white;
    cursor: pointer;
    transition: all 0.3s ease;
    border: 2px solid #e0e0e0;
}

.profile-trigger:hover {
    border-color: #6B5DD3;
    box-shadow: 0 4px 12px rgba(107, 93, 211, 0.2);
}

.profile-avatar {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    object-fit: cover;
}

.profile-dropdown {
    position: absolute;
    right: 0;
    top: 50px;
    background: white;
    border-radius: 12px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
    min-width: 200px;
    z-index: 1000;
}

.profile-dropdown a {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 14px 20px;
    color: #333;
    text-decoration: none;
    transition: background 0.2s ease;
    border-bottom: 1px solid #f0f0f0;
}

.profile-dropdown a:last-child {
    border-bottom: none;
}

.profile-dropdown a:hover {
    background: #f8f9ff;
    color: #6B5DD3;
}
```

#### C. Add Profile JavaScript Functions

```javascript
function toggleProfileMenu() {
    const dropdown = document.getElementById('profileDropdown');
    dropdown.style.display = dropdown.style.display === 'none' ? 'block' : 'none';
}

// Close dropdown when clicking outside
document.addEventListener('click', function(event) {
    const container = document.querySelector('.profile-menu-container');
    if (container && !container.contains(event.target)) {
        document.getElementById('profileDropdown').style.display = 'none';
    }
});

function openManageProfile() {
    switchTab('profile');
    document.getElementById('profileDropdown').style.display = 'none';
}

async function handleLogout() {
    try {
        await fetch('/api/logout', {
            method: 'POST',
            credentials: 'include'
        });
        window.location.href = '/';
    } catch (err) {
        console.error('Logout error:', err);
        window.location.href = '/';
    }
}

// Load profile name on page load
function loadProfileInfo() {
    fetch('/api/profile', { credentials: 'include' })
        .then(res => res.json())
        .then(data => {
            const name = data.first_name || data.email.split('@')[0];
            document.getElementById('profileName').textContent = name;
        });
}

// Add to window.addEventListener('load')
window.addEventListener('load', () => {
    loadSettings();
    updateStats();
    loadCredits();
    loadProfileInfo();  // ADD THIS
});
```

---

### Phase 6: Add "Manage Profile" Tab

**Add new tab in dashboard.html after Settings tab:**

```html
<!-- Profile Tab -->
<div id="profileTab" class="tab-content">
    <div class="card">
        <h2><span class="card-icon">👤</span> Manage Profile</h2>

        <div class="form-group">
            <label for="profileFirstName">First Name</label>
            <input type="text" id="profileFirstName" />
        </div>

        <div class="form-group">
            <label for="profileLastName">Last Name</label>
            <input type="text" id="profileLastName" />
        </div>

        <div class="form-group">
            <label for="profileEmail">Email (cannot be changed)</label>
            <input type="email" id="profileEmail" disabled style="background: #f0f0f0;" />
        </div>

        <h3 style="margin-top: 30px; margin-bottom: 20px;">Change Password</h3>

        <div class="form-group">
            <label for="currentPassword">Current Password</label>
            <input type="password" id="currentPassword" />
        </div>

        <div class="form-group">
            <label for="newPassword">New Password</label>
            <input type="password" id="newPassword" />
        </div>

        <div class="form-group">
            <label for="confirmPassword">Confirm New Password</label>
            <input type="password" id="confirmPassword" />
        </div>

        <button class="btn" onclick="updateProfile()">Save Profile Changes</button>
    </div>
</div>
```

**Add JavaScript functions:**

```javascript
function loadProfileTab() {
    fetch('/api/profile', { credentials: 'include' })
        .then(res => res.json())
        .then(data => {
            document.getElementById('profileFirstName').value = data.first_name || '';
            document.getElementById('profileLastName').value = data.last_name || '';
            document.getElementById('profileEmail').value = data.email;
        });
}

async function updateProfile() {
    const firstName = document.getElementById('profileFirstName').value;
    const lastName = document.getElementById('profileLastName').value;
    const currentPassword = document.getElementById('currentPassword').value;
    const newPassword = document.getElementById('newPassword').value;
    const confirmPassword = document.getElementById('confirmPassword').value;

    // Validate password change if provided
    if (newPassword) {
        if (!currentPassword) {
            alert('❌ Please enter your current password');
            return;
        }
        if (newPassword !== confirmPassword) {
            alert('❌ New passwords do not match');
            return;
        }
        if (newPassword.length < 8) {
            alert('❌ Password must be at least 8 characters');
            return;
        }
    }

    try {
        const res = await fetch('/api/update_profile', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({
                first_name: firstName,
                last_name: lastName,
                current_password: currentPassword,
                new_password: newPassword
            })
        });

        const data = await res.json();

        if (res.ok) {
            alert('✅ Profile updated successfully!');
            // Clear password fields
            document.getElementById('currentPassword').value = '';
            document.getElementById('newPassword').value = '';
            document.getElementById('confirmPassword').value = '';
            loadProfileInfo();  // Refresh name in dropdown
        } else {
            alert('❌ Error: ' + (data.error || 'Failed to update profile'));
        }
    } catch (err) {
        alert('❌ Error: ' + err.message);
    }
}

// Update switchTab function to include profile tab
if (tabName === 'profile') loadProfileTab();
```

---

### Phase 7: Add Profile Update Endpoint in app_v3.py

```python
@app.route('/api/update_profile', methods=['POST'])
@login_required
def update_profile():
    """Update user profile (name, password)"""
    try:
        data = request.json
        user = User.query.get(current_user.id)

        # Update name fields
        if 'first_name' in data:
            user.first_name = data['first_name']
        if 'last_name' in data:
            user.last_name = data['last_name']

        # Update password if provided
        if data.get('new_password'):
            if not data.get('current_password'):
                return jsonify({"error": "Current password required"}), 400

            if not user.check_password(data['current_password']):
                return jsonify({"error": "Current password is incorrect"}), 401

            user.set_password(data['new_password'])

        db.session.commit()
        return jsonify({"message": "Profile updated successfully"}), 200

    except Exception as e:
        logger.error(f"Error updating profile: {e}")
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
```

---

### Phase 8: Create Migration Script

**File: `migrate_to_credit_system.py`**

```python
"""
Migration script to convert existing users from dollar-based to credit-based system
Run this ONCE after deploying credit system changes
"""
from app_v3 import app, db, User, CreditTransaction
from credit_system import calculate_credits_from_purchase

def migrate_all_users():
    """Convert all users from dollar balance to credit balance"""
    with app.app_context():
        users = User.query.all()

        print(f"Found {len(users)} users to migrate")
        print("=" * 60)

        for user in users:
            old_balance = user.credit_balance

            if isinstance(old_balance, float):
                # Convert dollar amount to credits at base rate ($1.99/article)
                # This is a conservative conversion
                credits = int(old_balance / 1.99)

                print(f"User {user.id} ({user.email}):")
                print(f"  Old balance: ${old_balance:.2f}")
                print(f"  New balance: {credits} credits")

                user.credit_balance = credits

                # Create migration transaction record
                transaction = CreditTransaction(
                    user_id=user.id,
                    amount=credits - int(old_balance),  # Difference
                    transaction_type='migration',
                    balance_after=credits,
                    description=f'System migration: ${old_balance:.2f} converted to {credits} credits'
                )
                db.session.add(transaction)

        db.session.commit()
        print("=" * 60)
        print("✅ Migration complete!")

if __name__ == "__main__":
    confirm = input("⚠️  This will convert all user balances. Type 'MIGRATE' to confirm: ")
    if confirm == 'MIGRATE':
        migrate_all_users()
    else:
        print("Migration cancelled")
```

---

## TESTING CHECKLIST

After implementing all changes:

- [ ] Delete test user: `python delete_user.py ezautobuying@gmail.com`
- [ ] Run migration script: `python migrate_to_credit_system.py`
- [ ] Register new user - verify 3 welcome credits received
- [ ] Purchase $25 package - verify 12 credits added
- [ ] Purchase $100 package - verify 57 credits added
- [ ] Purchase $500 package - verify 400 credits added
- [ ] Generate article - verify 1 credit deducted
- [ ] Check transaction history - verify shows credits not dollars
- [ ] Test profile dropdown menu
- [ ] Test password change
- [ ] Test logout
- [ ] Verify new branding and colors throughout

---

## DEPLOYMENT STEPS

1. **Backup database** before making any changes
2. **Update all files** as described above
3. **Run migration script** to convert existing users
4. **Test thoroughly** with new user registration
5. **Update DNS** to point my.contentgenerator.me to 72.60.163.46
6. **Update Stripe webhook URLs** in Stripe Dashboard for production

---

## FILES THAT NEED CHANGES

1. ✅ `credit_system.py` - DONE
2. ⏳ `static/dashboard.html` - Credit packages, display, colors, branding, profile menu
3. ⏳ `app_v3.py` - Add `/api/update_profile` endpoint, update default brand colors
4. ✅ `delete_user.py` - CREATED
5. ⏳ `migrate_to_credit_system.py` - CREATE THIS
6. ⏳ Logo images - Already provided by user

---

This guide provides a complete roadmap for finishing the implementation. Each section can be done independently and tested.
