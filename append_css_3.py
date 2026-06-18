import os

css_append = """
/* ================================================================
   MOBILE TWEAKS - SHOW SOCIAL ICONS
   ================================================================ */

@media (max-width: 768px) {
  /* Restore the social wrap, but remove its fixed width and background shape */
  .nav-social-wrap {
    display: flex !important;
    width: auto;
    flex: 1;
    align-items: center;
  }
  .nav-shape-svg {
    display: none !important; /* Hide the background SVG */
  }
  .nav-social-icons {
    display: flex !important;
    justify-content: center;
    width: 100%;
    margin-bottom: 0;
  }
  
  /* Hide youtube icon to save space, user requested Instagram and Facebook */
  #nav-yt-left {
    display: none !important;
  }
  
  .social-icon {
    width: 32px;
    height: 32px;
    font-size: 14px;
    margin: 0 5px;
  }
}
"""

file_path = "c:\\Users\\jasil_myg\\Desktop\\BIGBOSS\\static\\style.css"
with open(file_path, "a", encoding="utf-8") as f:
    f.write(css_append)

print("Appended social icons mobile CSS")
