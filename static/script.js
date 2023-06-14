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
              messagesContainer.append('<li><strong>' + sender + '</strong> ' + message + '</li>');
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

  $('#register-submit').on('click', function() {
      var username = $('#username-input').val().trim();
      //var email = $('#email-input').val().trim();
      var password = $('#password-input').val().trim();

      // Create an object with the registration data
      var registrationData = {
          username: username,
          //email: email,
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
              // TODO: Handle the response accordingly (e.g., display a success message, redirect to a new page, etc.)
          },
          error: function(error) {
              // Handle the error response from the server
              console.error(error); // Log the error for debugging purposes
              // TODO: Handle the error accordingly (e.g., display an error message to the user)
          }
      });
  });

  // Event listener for the name submit button click
  $('#name-submit').on('click', function() {
      setUsername();
  });

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

  // Event listener for receiving a new message from the server
  socket.on('message', function(data) {
      var message = escapeHtml(data.message);
      var sender = escapeHtml(data.name);
      $('#messages').append('<li><strong>' + sender + '</strong> ' + message + '</li>');
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
