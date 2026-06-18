import os

css_append = """
/* ================================================================
   MOBILE TWEAKS FROM USER FEEDBACK
   ================================================================ */

@media (max-width: 768px) {
  /* Hide the top-nav svg shapes and outline so logos don't get pushed out */
  .nav-social-wrap { display: none !important; }
  
  /* Make the nav full width for the two logos */
  .top-nav { justify-content: space-between; }
  
  /* Hide the duplicate logo in the registration section */
  .reg-bb-img { display: none !important; }
  
  /* Hide the giant host image on mobile so the form is immediately accessible */
  .reg-host-container { display: none !important; }
  
  /* Reduce the padding on the form card to fit nicely */
  .form-card { padding: 20px 15px 40px 15px; margin-top: -30px; }
  
  /* The hero section title */
  .hero-left {
     padding-top: 20px;
  }
}
"""

file_path = "c:\\Users\\jasil_myg\\Desktop\\BIGBOSS\\static\\style.css"
with open(file_path, "a", encoding="utf-8") as f:
    f.write(css_append)

print("Appended more CSS")
