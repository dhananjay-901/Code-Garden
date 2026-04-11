📝 Notes App A lightweight, local-storage-powered, Markdown-enabled notes application built with vanilla HTML, CSS, and JavaScript. This app allows you to create, edit, preview, search, and delete notes—all stored directly in the browser.

🚀 Features Markdown Editor Write - notes in Markdown and toggle between Edit and Preview modes. Local Storage Persistence - All notes are stored in localStorage, so they remain even after closing the browser. Wiki-Style Links - Supports [[double bracket]] links to other notes (non-navigating placeholder UI included). Search - Live search across titles and content. Beautiful UI - Clean, modern, dark-themed layout inspired by contemporary note apps. Note Management - Create, select, and delete notes with ease (with protection against deleting the last note).

📂 Project Structure This project is contained in a single HTML file: notes.html It includes: Inline CSS for styling JavaScript for application logic HTML layout (sidebar + editor/preview workspace)

🛠️ How It Works State Management The app stores: notes: Array of note objects (id, title, content, created) activeNoteId: Which note is currently selected editMode: Whether the editor or preview is active searchQuery: Live filter value

Markdown Rendering A minimal Markdown renderer is implemented with regex, supporting: #, ##, ### headings,bold, italic, bold+italic, inline code, Line breaks, Wiki-style links [[like this]]

Storage: Notes are saved in: localStorage['notes-app-data'] localStorage['notes-app-active'] UI Components Sidebar (search, create note, list of notes) Editor and preview panel Delete buttons on hover Mode buttons (Edit / Preview)

▶️ Getting Started

Open the App Simply open the file in a browser: notes.html no build step, no dependencies.
Start Taking Notes Click + New Note Write using Markdown Switch to Preview to see rendered output
🧩 Customization Feel free to modify: Styles (contained inside <style>) Markdown renderer (renderMarkdown function) LocalStorage keys Default example note Sidebar width, font styles, note behavior, etc.

🐞 Troubleshooting Notes not saving? make sure your browser allows localStorage for local files. Chrome may require launching with special flags or using a simple local server like: python3 -m http.server

LocalStorage full? Browsers limit localStorage to ~5MB; large notes may eventually exceed this.

📜 License

MIT License — free to use, modify, and distribute.
