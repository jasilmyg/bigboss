/* ── Registration Form JS ──────────────────── */

const API = '';  // same origin

// ── Helpers ──────────────────────────────────
function show(el)    { el && el.classList.remove('hidden'); }
function hide(el)    { el && el.classList.add('hidden'); }
function setErr(id, msg) {
  const el = document.getElementById(id);
  if (!el) return;
  el.textContent = msg;
  msg ? show(el) : hide(el);
  const baseId = id.replace('err-','');
  const input = document.querySelector(`[id^="${baseId}-"]`) ||
                document.querySelector(`[name="${baseId}"]`) ||
                document.querySelector(`#${baseId}`);
  if (input) {
    msg ? input.classList.add('input-error') : input.classList.remove('input-error');
  }
}
function clearErr(id) { setErr(id, ''); }

// ── OTP Flow ─────────────────────────────────
let phoneVerified = false;

const sendOtpBtn   = document.getElementById('send-otp-btn');
const verifyOtpBtn = document.getElementById('verify-otp-btn');
const otpRow       = document.getElementById('otp-verify-row');
const otpStatus    = document.getElementById('otp-status');
const phoneInput   = document.getElementById('contact-number');
const otpInput     = document.getElementById('otp-input');

function showOtpStatus(msg, type) {
  // type: 'success' | 'error' | 'info'
  otpStatus.textContent = msg;
  otpStatus.className = `otp-status ${type}`;
  show(otpStatus);
}

if (sendOtpBtn) {
  sendOtpBtn.addEventListener('click', async () => {
    const phone = phoneInput.value.trim();
    if (!phone || phone.length !== 10 || !/^\d{10}$/.test(phone)) {
      setErr('err-contact', 'Enter a valid 10-digit mobile number.');
      return;
    }
    clearErr('err-contact');
    sendOtpBtn.disabled = true;
    sendOtpBtn.textContent = 'SENDING…';

    try {
      const res  = await fetch(`${API}/api/send-otp`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phone }),
      });
      const data = await res.json();

      if (data.success) {
        show(otpRow);
        showOtpStatus(
          data.dev_otp
            ? `OTP sent ✓  (Dev mode – OTP: ${data.dev_otp})`
            : 'OTP sent to your number.',
          'info'
        );
        startResendTimer(sendOtpBtn);
      } else {
        setErr('err-contact', data.message || 'Failed to send OTP.');
        sendOtpBtn.disabled = false;
        sendOtpBtn.textContent = 'SEND OTP';
      }
    } catch (e) {
      setErr('err-contact', 'Network error. Please try again.');
      sendOtpBtn.disabled = false;
      sendOtpBtn.textContent = 'SEND OTP';
    }
  });
}

function startResendTimer(btn) {
  let secs = 30;
  btn.textContent = `RESEND (${secs}s)`;
  const t = setInterval(() => {
    secs--;
    btn.textContent = secs > 0 ? `RESEND (${secs}s)` : 'RESEND OTP';
    if (secs <= 0) { clearInterval(t); btn.disabled = false; }
  }, 1000);
}

if (verifyOtpBtn) {
  verifyOtpBtn.addEventListener('click', async () => {
    const phone = phoneInput.value.trim();
    const otp   = otpInput.value.trim();
    if (!otp || otp.length < 6) {
      showOtpStatus('Enter the 6-digit OTP.', 'error');
      return;
    }
    verifyOtpBtn.disabled = true;
    verifyOtpBtn.textContent = 'CHECKING…';

    try {
      const res  = await fetch(`${API}/api/verify-otp`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phone, otp }),
      });
      const data = await res.json();

      if (data.success) {
        phoneVerified = true;
        showOtpStatus('✓ Phone verified!', 'success');
        hide(otpRow);
        verifyOtpBtn.textContent = 'VERIFY';
        phoneInput.readOnly = true;
        phoneInput.style.opacity = '0.7';
        sendOtpBtn.disabled = true;
        sendOtpBtn.textContent = '✓ VERIFIED';
        sendOtpBtn.style.background = 'linear-gradient(135deg,#1b5e20,#2e7d32)';
      } else {
        showOtpStatus(data.message || 'Invalid OTP.', 'error');
        verifyOtpBtn.disabled = false;
        verifyOtpBtn.textContent = 'VERIFY';
      }
    } catch (e) {
      showOtpStatus('Network error. Please try again.', 'error');
      verifyOtpBtn.disabled = false;
      verifyOtpBtn.textContent = 'VERIFY';
    }
  });
}

// ── Video Upload ──────────────────────────────
const videoInput    = document.getElementById('intro-video');
const videoSelected = document.getElementById('video-selected');
const videoFilename = document.getElementById('video-filename');
const removeVideoBtn = document.getElementById('remove-video-btn');

if (videoInput) {
  videoInput.addEventListener('change', () => {
    const file = videoInput.files[0];
    if (file) {
      videoFilename.textContent = `📎 ${file.name}  (${(file.size/1024/1024).toFixed(1)} MB)`;
      show(videoSelected);
    }
  });
}

if (removeVideoBtn) {
  removeVideoBtn.addEventListener('click', () => {
    videoInput.value = '';
    hide(videoSelected);
  });
}

// ── Form Validation ───────────────────────────
function validate() {
  let ok = true;
  let fails = [];

  const phone = phoneInput ? phoneInput.value.trim() : '';
  if (!phone || !/^\d{10}$/.test(phone)) {
    setErr('err-contact', 'Enter a valid 10-digit mobile number.'); ok = false; fails.push('contact');
  } else { clearErr('err-contact'); }

  const fullName = document.getElementById('full-name');
  if (!fullName || !fullName.value.trim()) {
    setErr('err-fullname', 'Full name is required.'); ok = false; fails.push('fullname');
  } else { clearErr('err-fullname'); }

  const age = document.getElementById('age');
  const ageVal = age ? parseInt(age.value, 10) : NaN;
  if (!age || isNaN(ageVal) || ageVal < 18 || ageVal > 99) {
    setErr('err-age', 'Must be 18 or older.'); ok = false; fails.push('age');
  } else { clearErr('err-age'); }

  const gender = document.getElementById('gender');
  if (!gender || !gender.value) {
    setErr('err-gender', 'Please select a gender.'); ok = false; fails.push('gender');
  } else { clearErr('err-gender'); }

  const email = document.getElementById('email');
  const emailRe = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!email || !emailRe.test(email.value.trim())) {
    setErr('err-email', 'Enter a valid email address.'); ok = false; fails.push('email');
  } else { clearErr('err-email'); }

  const city = document.getElementById('city');
  if (!city || !city.value.trim()) {
    setErr('err-city', 'City is required.'); ok = false; fails.push('city');
  } else { clearErr('err-city'); }

  const about = document.getElementById('about-yourself');
  if (!about || about.value.trim().length < 20) {
    setErr('err-about', 'Please write at least 20 characters.'); ok = false; fails.push('about');
  } else { clearErr('err-about'); }

  const c1 = document.querySelector('input[name="consent1"]:checked');
  if (!c1) {
    setErr('err-consent1', 'Please select an option.'); ok = false; fails.push('consent1_empty');
  } else if (c1.value !== 'agree') {
    setErr('err-consent1', 'You must agree to participate.'); ok = false; fails.push('consent1_not_agree');
  } else { clearErr('err-consent1'); }

  const c2 = document.querySelector('input[name="consent2"]:checked');
  if (!c2) {
    setErr('err-consent2', 'Please select an option.'); ok = false; fails.push('consent2_empty');
  } else if (c2.value === 'disagree') {
    setErr('err-consent2', 'You must agree to the Privacy Notice.'); ok = false; fails.push('consent2_disagree');
  } else { clearErr('err-consent2'); }

  window.__fails = fails;
  return ok;
}

// ── Form Submit ───────────────────────────────
const form      = document.getElementById('registration-form');
const submitBtn = document.getElementById('submit-btn');
const submitTxt = document.getElementById('submit-btn-text');
const globalErr = document.getElementById('form-error-global');
const successScreen = document.getElementById('success-screen');

if (form) {
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    hide(globalErr);

    if (!validate()) {
      globalErr.textContent = 'Please fix the errors above before submitting. (' + window.__fails.join(', ') + ')';
      show(globalErr);
      // Scroll to first error
      const firstErr = document.querySelector('.error-msg:not(.hidden)');
      firstErr && firstErr.scrollIntoView({ behavior: 'smooth', block: 'center' });
      return;
    }

    submitBtn.disabled = true;
    submitTxt.textContent = 'PREPARING UPLOAD...';
    
    // Hide form, show progress screen immediately
    hide(form);
    const progressScreen = document.getElementById('progress-screen');
    const progressBarFill = document.getElementById('progress-bar-fill');
    const progressPercent = document.getElementById('progress-percent');
    const progressSize = document.getElementById('progress-size');
    show(progressScreen);
    progressScreen.scrollIntoView({ behavior: 'smooth' });

    try {
      const fd = new FormData(form);

      const xhr = new XMLHttpRequest();
      xhr.open('POST', `${API}/api/register`, true);

      // Setup progress event
      xhr.upload.addEventListener('progress', (e) => {
        if (e.lengthComputable) {
          const percentComplete = Math.round((e.loaded / e.total) * 100);
          progressBarFill.style.width = percentComplete + '%';
          progressPercent.textContent = percentComplete + '%';
          
          const loadedMB = (e.loaded / (1024 * 1024)).toFixed(1);
          const totalMB = (e.total / (1024 * 1024)).toFixed(1);
          progressSize.textContent = `${loadedMB} MB / ${totalMB} MB`;
        }
      });

      const data = await new Promise((resolve, reject) => {
        xhr.onload = () => {
          try {
            const parsed = JSON.parse(xhr.responseText);
            resolve(parsed);
          } catch (err) {
            if (xhr.status >= 200 && xhr.status < 300) {
              reject(new Error(`Server returned non-JSON response: ${xhr.status}`));
            } else {
              reject(new Error(`Server returned ${xhr.status}: The file might be too large or the server timed out.`));
            }
          }
        };
        xhr.onerror = () => reject(new Error('Network error. Please check your connection and try again.'));
        xhr.send(fd);
      });

      if (data.success) {
        // Show success
        hide(progressScreen);
        show(successScreen);
        successScreen.scrollIntoView({ behavior: 'smooth' });
      } else {
        hide(progressScreen);
        show(form);
        const msgs = data.errors ? data.errors.join(' • ') : (data.message || 'Submission failed.');
        globalErr.textContent = msgs;
        show(globalErr);
        submitBtn.disabled = false;
        submitTxt.textContent = "I'M READY FOR AGNIPAREEKSHA!";
      }
    } catch (err) {
      console.error(err);
      hide(progressScreen);
      show(form);
      globalErr.textContent = err.message || 'Network error. Please check your connection and try again.';
      show(globalErr);
      submitBtn.disabled = false;
      submitTxt.textContent = "I'M READY FOR AGNIPAREEKSHA!";
    }
  });
}

// ── Clear errors on input ─────────────────────
document.querySelectorAll('.form-input').forEach(input => {
  input.addEventListener('input', () => {
    input.classList.remove('input-error');
    const name = input.name || input.id;
    const errEl = document.getElementById(`err-${name}`) ||
                  document.getElementById(`err-${input.id}`);
    if (errEl) hide(errEl);
  });
});
