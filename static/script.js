$(document).ready(function() {
  var socket = io.connect(window.location.origin);
  var name = '';
  var errorVisible = false;

  function escapeHtml(content) {
      return $('<div>').text(content).html();
  }

  // Scroll to the bottom of the messages list
  function scrollToBottom() {
      var messagesList = document.getElementById('messages');
      messagesList.scrollTop = messagesList.scrollHeight;
  }

  // Show the name input form and hide the chat form
  function showNameForm() {
      $('#name-form').show();
      $('#chat-form').hide();
  }

  // Show the chat form and scroll to the bottom of the messages list
  function showChatForm() {
      $('#name-form').hide();
      $('#register-form').hide();
      $('#register-buttom').hide();
      $('#chat-form').show();
      scrollToBottom();
  }

  // Display the chat history
  function showChatHistory(messages) {
      var messagesContainer = $('#messages');
      if (messages.length > 0) {
          $('#no-messages').hide(); // Hide the "No messages yet" message

          for (var i = 0; i < messages.length; i++) {
              var message = messages[i].message;
              var sender = messages[i].name;
              var color = sender.toString().split("-");
              color = CryptoJS.MD5(color[2]).toString().substring(0, 6);
              messagesContainer.append('<li><strong style="color: #' + color + '">' + sender + '</strong> ' + message + '</li>');
          }

          // Scroll to the last message
          messagesContainer.scrollTop(messagesContainer.prop('scrollHeight'));
      } else {
          $('#no-messages').show(); // Show the "No messages yet" message
      }

      scrollToBottom();
  }

  // Display an error message
  function displayErrorMessage(message) {
      $('#error-message').text(message);
      $('#error-message').show();
      errorVisible = true;
  }

  // Hide the error message
  function hideErrorMessage() {
      $('#error-message').hide();
      errorVisible = false;
  }

  // Send a message
  function sendMessage() {
      var messageInput = $('#message');
      var message = messageInput.val().trim();

      if (message !== '') {
          var escapedMessage = escapeHtml(message);
          socket.emit('message', { 'message': escapedMessage });
          messageInput.val('');
          hideErrorMessage();

          // Remove the information message
          $('#no-messages').remove();
      } else {
          displayErrorMessage('Por favor, introduce un mensaje.');
      }
  }

  // Set the username
  function setUsername() {
      var username = $('#name-input').val().trim();
      if (username !== '') {
          name = username;
          socket.emit('set_name', name);
          showChatForm();
          if (errorVisible) {
              hideErrorMessage();
          }
      } else {
          displayErrorMessage('Por favor, introduce un usuario.');
      }
  }

  // Event listener for the register buttom
  $('#register-buttom').on('click', function() {
      $('#register-form').show(); // Show the registration form
  });

  $('#name-submit').on('click', function() {
    var username = $('#name-input').val().trim();
    var password = $('#password-login-input').val().trim();

    // Create an object with the login data
    var loginData = {
        username: username,
        password: password
    };

    // Send the login data to the back-end using AJAX
    $.ajax({
        type: 'POST',
        url: '/login', // Update with the appropriate URL for your back-end route
        data: loginData,
        success: function(response) {
            // Handle the success response from the server
            console.log(response); // Log the response for debugging purposes
    
            if (response.result === 'success') {
                // Redirect to the home page or perform any other desired action
                setUsername();
            } else {
                // Display the error message
                displayLoginErrorMessage(response.message);
            }
        },
        error: function(xhr, status, error) {
            // Handle the error response from the server
            console.error(error); // Log the error for debugging purposes
    
            // Display the error message
            displayLoginErrorMessage('An error occurred. Please try again.');
        }
    });
});
function displayLoginErrorMessage(message) {
    // Set the error message text
    $('#login-error').text(message);

    // Show the error message
    $('#login-error').show();

    // Hide the error message after a certain duration (e.g., 5 seconds)
    setTimeout(function() {
        $('#login-error').hide();
    }, 5000);
}


  $('#register-submit').on('click', function() {
    var username = $('#username-register-input').val().trim();
    var hash = $('#hash-register-input').val().trim();
    var password = $('#password-register-input').val().trim();

    // Create an object with the registration data
    var registrationData = {
        username: username,
        hash: hash,
        password: password
    };

    // Send the registration data to the back-end using AJAX
    $.ajax({
        type: 'POST',
        url: '/register', // Update with the appropriate URL for your back-end route
        data: registrationData,
        success: function(response) {
            // Handle the success response from the server
            console.log(response); // Log the response for debugging purposes
    
            if (response.result === "create") {
                // Display the success message
                displaySuccessMessage(response.message);
            } else {
                // Display the error message
                displayErrorMessage(response.message);
            }
        },
        error: function(xhr, status, error) {
            // Handle the error response from the server
            console.error(error); // Log the error for debugging purposes
    
            // Display the error message
            displayErrorMessage('An error occurred. Please try again.');
        }
    });
});
  // Function to display the success message
function displaySuccessMessage(message) {
    // Set the success message text
    $('#user-success-message').text(message);

    // Show the success message
    $('#user-success-message').show();

    // Hide the success message after a certain duration (e.g., 3 seconds)
    setTimeout(function() {
        $('#user-success-message').hide();
    }, 5000);
}

// Function to display the error message
function displayErrorMessage(message) {
    // Set the error message text
    $('#register-error-message').text(message);

    // Show the error message
    $('#register-error-message').show();

    // Hide the error message after a certain duration (e.g., 5 seconds)
    setTimeout(function() {
        $('#register-error-message').hide();
    }, 5000);
}

  //// Event listener for the name submit button click
  //$('#name-submit').on('click', function() {
  //    setUsername();
  //});

  // Event listener for the name input field keypress
  $('#name-input').on('keypress', function(event) {
      if (event.which === 13) {
          event.preventDefault();
          setUsername();
      }
  });

  // Event listener for receiving chat history from the server
  socket.on('chat_history', function(messages) {
      showChatHistory(messages);
  });

// Define a map to store the calculated colors for senders
var senderColors = {};

socket.on('message', function(data) {
  var message = escapeHtml(data.message);
  var sender = escapeHtml(data.name);
//   var nameParts = sender.split("-");
//   var senderToHash = nameParts[2]; // Assuming [1] is the desired part for hashing

//   // Calculate the hash only if it hasn't been calculated before for this sender
//   if (!senderColors.hasOwnProperty(senderToHash)) {
//     var hash = CryptoJS.MD5(senderToHash);
//     var color = hash.toString().substring(0, 6); // Convert hash to string before substring
//     senderColors[senderToHash] = color;
//   }

//   var color = senderColors[senderToHash]; // Retrieve the color for the sender
  
  var color = sender.toString().split("-");
  color = CryptoJS.MD5(color[2]).toString().substring(0, 6);
  var listItem = $('<li></li>').html('<strong style="color: #' + color + '">' + sender + '</strong> ' + message);
  $('#messages').append(listItem);
  scrollToBottom();
});

  // Event listener for the send button click
  $('#send').on('click', function() {
      sendMessage();
  });

  // Event listener for the message input field keypress
  $('#message').on('keypress', function(event) {
      if (event.which === 13) {
          event.preventDefault();
          if ($('#message').val().trim() !== '') {
              sendMessage();
          } else {
              if (errorVisible) {
                  hideErrorMessage();
              }
              displayErrorMessage('Please enter a message.');
          }
      } else {
          if (errorVisible) {
              hideErrorMessage();
          }
      }
  });

  // Event listener for the error message close button click
  $('#error-close').on('click', function() {
      hideErrorMessage();
  });

  // Show the name input form initially
  showNameForm();
});
