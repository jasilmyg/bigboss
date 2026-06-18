import os

css_append = """
/* ================================================================
   MOBILE RESPONSIVENESS & MEDIA QUERIES
   ================================================================ */

/* Tablet & Smaller Laptops */
@media (max-width: 1024px) {
  .hero-content {
    flex-direction: column;
    padding-top: 40px;
    align-items: center;
  }
  .hero-left {
    padding-left: 0;
    margin-bottom: 40px;
  }
  
  .reg-layout {
    flex-direction: column;
    padding-top: 80px;
  }
  .reg-left, .reg-right {
    width: 100%;
    padding: 20px;
  }
  .reg-host-container {
    position: static;
    transform: none;
    justify-content: center;
    margin-bottom: -60px;
    z-index: 0;
  }
  .reg-host-img {
    max-height: 400px;
    transform: none;
  }
  .ghost-text {
    font-size: 50px;
  }
}

/* Mobile Devices */
@media (max-width: 768px) {
  .top-nav {
    padding: 0 15px;
    height: 60px;
  }
  .myg-logo, .hotstar-logo {
    height: 40px;
    margin-right: 15px;
  }
  .nav-social-icons {
    gap: 10px;
  }
  .social-icon {
    width: 28px;
    height: 28px;
    font-size: 14px;
  }
  .outline-wrap { margin-left: 0; }
  .solid-wrap { margin-right: 0; }
  
  .hero-title {
    font-size: clamp(28px, 6vw, 40px);
  }
  .hero-tagline {
    font-size: clamp(18px, 4vw, 24px);
  }
  
  .bb-logo-img {
    transform: scale(1);
    margin: 10px 0;
  }
  
  .form-card {
    padding: 20px 20px 60px 20px;
  }
  .form-row-2 {
    grid-template-columns: 1fr;
  }
  
  .hero-glow-1 {
    width: 300px; height: 300px;
  }
  .hero-glow-2 {
    width: 250px; height: 250px;
  }
  
  /* Make sure video upload button doesn't overflow */
  .video-upload-box {
    flex-direction: column;
    text-align: center;
    gap: 15px;
  }
  .upload-video-btn {
    width: 100%;
  }
}

/* Very Small Phones */
@media (max-width: 480px) {
  .top-nav {
    padding: 0 10px;
  }
  .myg-logo, .hotstar-logo {
    height: 30px;
  }
  .nav-social-icons {
    display: none; /* Hide social icons on very small screens to save space */
  }
  .form-card {
    padding: 15px 15px 50px 15px;
  }
  .reg-host-img {
    max-height: 250px;
  }
  .ghost-text {
    font-size: 30px;
    letter-spacing: 5px;
  }
}
"""

file_path = "c:\\Users\\jasil_myg\\Desktop\\BIGBOSS\\static\\style.css"
with open(file_path, "a", encoding="utf-8") as f:
    f.write(css_append)

print("Appended media queries to style.css")
