$(document).ready(function() {
    var socket = io.connect(window.location.origin);
    var name = '';
    var errorVisible = false;
  
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
          messagesContainer.append('<li><strong>' + sender + ':</strong> ' + message + '</li>');
        }
        
        // Scroll to the last message
        messagesContainer.scrollTop(messagesContainer.prop("scrollHeight"));
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
        socket.emit('message', { 'message': message });
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
      var message = data.message;
      var sender = data.name;
      $('#messages').append('<li><strong>' + sender + ':</strong> ' + message + '</li>');
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
  