// vote-interactions.js
// Enhances the single event voting UX: immediate option highlight and submit de‑duplication.
// Progressive enhancement only – server logic remains authoritative.

(function(){
  document.addEventListener('DOMContentLoaded', function(){
    var ballot = document.getElementById('ballot');
    if(!ballot) return;
    var form = ballot.querySelector('form');
    if(!form) return; // Closed period or creator disabled state may have no form

    var optionLabels = form.querySelectorAll('label.vote-option');
    optionLabels.forEach(function(label){
      var radio = label.querySelector('input[type="radio"]');
      if(!radio) return;
      radio.addEventListener('change', function(){
        optionLabels.forEach(function(l){ l.classList.remove('vote-option--selected'); });
        label.classList.add('vote-option--selected');
      });
      // Also allow clicking anywhere on label to select (for browsers without implicit behavior)
      label.addEventListener('click', function(e){
        var r = label.querySelector('input[type="radio"]');
        if(r && !r.checked){
          r.checked = true;
          r.dispatchEvent(new Event('change', { bubbles: true }));
        }
      });
    });

    // Prevent double submissions (Update Vote / Submit Vote / Retract) – disable all submit buttons
    form.addEventListener('submit', function(){
      var buttons = form.querySelectorAll('button[type="submit"]');
      buttons.forEach(function(btn){
        if(!btn.disabled){
          btn.dataset.originalText = btn.textContent;
          btn.textContent = 'Submitting...';
          btn.disabled = true;
          btn.classList.add('opacity-70','cursor-not-allowed');
        }
      });
    }, { once: true });
  });
})();
