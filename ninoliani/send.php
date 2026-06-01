<?php

use PHPMailer\PHPMailer\PHPMailer;
use PHPMailer\PHPMailer\Exception;
use Dotenv\Dotenv;

require __DIR__ . '/vendor/autoload.php';

$dotenv = Dotenv::createImmutable(__DIR__);
$dotenv->load();

header('Content-Type: application/json');

try {

    $mail = new PHPMailer(true);

    $mail->isSMTP();
    $mail->Host = 'smtp.gmail.com';
    $mail->SMTPAuth = true;

    $mail->Username = $_ENV['GMAIL_EMAIL'];
    $mail->Password = $_ENV['GMAIL_PASS'];

    $mail->SMTPSecure = PHPMailer::ENCRYPTION_STARTTLS;
    $mail->Port = 587;

    $mail->setFrom($_ENV['GMAIL_EMAIL'], 'Website Form');
    $mail->addAddress($_ENV['GMAIL_EMAIL']);

    $mail->isHTML(true);
    $mail->Subject = "New message from site";

    $mail->Body = "
        <h3>New form message</h3>
        <p><b>Name:</b> {$_POST['fullName']}</p>
        <p><b>Phone:</b> {$_POST['phone']}</p>
        <p><b>Email:</b> {$_POST['email']}</p>
        <p><b>Comment:</b> {$_POST['comment']}</p>
    ";

    $mail->send();

    echo json_encode([
        "status" => "success"
    ]);

} catch (Exception $e) {

    echo json_encode([
        "status" => "error",
        "message" => $mail->ErrorInfo
    ]);
}