# Encrypting Customer Input in Flows

## Overview

Amazon Connect can encrypt sensitive DTMF input (credit card numbers, SSNs, account numbers) captured via the "Store customer input" block. Encryption happens client-side before the data reaches Connect, ensuring sensitive values are never stored or logged in plaintext within Connect.

---

## When to Encrypt

Encrypt input whenever the customer enters sensitive data via DTMF:

- **Credit card numbers** (PCI DSS requirement)
- **Social Security Numbers**
- **Bank account numbers**
- **PINs or passwords**
- **Any data classified as PII/sensitive by your compliance requirements**

If the input is non-sensitive (e.g., menu selection, zip code), encryption is unnecessary.

---

## How Encryption Works

### Step-by-Step

1. **Generate an RSA key pair** (2048-bit minimum, 4096-bit recommended)
2. **Upload the public key certificate** (X.509 format) to your Connect instance
3. **Configure the "Store customer input" block** with encryption enabled and the uploaded key selected
4. **Customer enters DTMF digits** during the call
5. **Connect encrypts the input** using the public key before storing it as a contact attribute
6. **Your Lambda function receives the encrypted attribute** and decrypts it using the private key
7. **Process and discard** — never log or persist the decrypted value

### Flow Configuration

In the "Store customer input" block:

- **Customer input type**: DTMF
- **Encrypt entry**: Enable
- **Encryption key**: Select the key you uploaded to the instance
- **Maximum digits**: Set appropriate limit (e.g., 16 for credit cards)
- **Encryption key ID certificate**: The X.509 certificate containing your public key

The encrypted value is stored in a contact attribute with the name you specify (e.g., `EncryptedCardNumber`). This attribute can be passed to a Lambda function.

---

## Key Management

### Generating the Key Pair

```bash
# Generate 4096-bit RSA private key
openssl genrsa -out private-key.pem 4096

# Generate public key certificate (X.509, valid for 1 year)
openssl req -new -x509 -key private-key.pem -out public-cert.pem -days 365 \
  -subj "/CN=ConnectEncryption/O=MyOrganization"
```

### Uploading the Public Key to Connect

Use the Amazon Connect console or the API:

```javascript
const { ConnectClient, AssociateSecurityKeyCommand } = require("@aws-sdk/client-connect");

const client = new ConnectClient({ region: "us-east-1" });

const result = await client.send(new AssociateSecurityKeyCommand({
  InstanceId: "your-instance-id",
  Key: "-----BEGIN CERTIFICATE-----\nMIID...your-cert-content...\n-----END CERTIFICATE-----"
}));

// result.AssociationId — save this for reference
```

### Listing Security Keys

```javascript
const { ListSecurityKeysCommand } = require("@aws-sdk/client-connect");

const keys = await client.send(new ListSecurityKeysCommand({
  InstanceId: "your-instance-id"
}));

// keys.SecurityKeys — array of { AssociationId, Key }
```

### Storing the Private Key

Store the private key securely. Never commit it to source control.

- **AWS Secrets Manager**: Store as a plaintext secret, retrieve in Lambda at runtime
- **AWS KMS**: Encrypt the private key file with a KMS key, decrypt in Lambda
- **AWS Systems Manager Parameter Store**: Store as a SecureString parameter

### Key Rotation

Rotate keys periodically (annually at minimum, quarterly for PCI compliance):

1. Generate a new key pair
2. Upload the new public certificate to Connect
3. Update the "Store customer input" block to use the new key
4. Update Lambda to use the new private key
5. Keep the old private key available temporarily to decrypt in-flight contacts
6. Disassociate the old key after the transition period

---

## Decryption in Lambda

When your Lambda function receives the encrypted attribute, decrypt it using the private key:

```javascript
const crypto = require("crypto");
const { GetSecretValueCommand, SecretsManagerClient } = require("@aws-sdk/client-secrets-manager");

const smClient = new SecretsManagerClient({ region: "us-east-1" });

exports.handler = async (event) => {
  const encryptedData = event.Details.ContactData.Attributes.EncryptedCardNumber;

  // Retrieve private key from Secrets Manager
  const secret = await smClient.send(new GetSecretValueCommand({
    SecretId: "connect/encryption-private-key"
  }));

  const privateKey = secret.SecretString;

  // Decrypt
  const decrypted = crypto.privateDecrypt(
    {
      key: privateKey,
      padding: crypto.constants.RSA_PKCS1_OAEP_PADDING,
      oaepHash: "sha256"
    },
    Buffer.from(encryptedData, "base64")
  );

  const cardNumber = decrypted.toString("utf8");

  // Process the card number (e.g., charge, validate)
  // NEVER log the decrypted value
  const lastFour = cardNumber.slice(-4);

  return {
    paymentStatus: "processed",
    lastFour: lastFour
  };
};
```

**Critical rules for the decryption Lambda**:

- Never `console.log()` the decrypted value
- Never return the full decrypted value in the Lambda response
- Never store the decrypted value in DynamoDB, S3, or any persistent store
- Process immediately and let it go out of scope

---

## PCI Compliance

When handling cardholder data (credit/debit card numbers), encryption is a PCI DSS requirement. Additional PCI considerations for Connect:

### DTMF Tone Masking

In the "Store customer input" block configuration:

- **Disable DTMF tones to agent**: Ensure the agent cannot hear the tones as the customer enters digits
- This prevents agents from reconstructing card numbers by listening to DTMF tones

### Do Not Store Decrypted Values in Contact Attributes

Contact attributes are logged in Contact Trace Records (CTRs) and flow logs. If you decrypt a value and store it back as a contact attribute, it appears in plaintext in CTRs. Only store masked versions (e.g., last four digits).

### Audit Trail

- **CloudTrail** logs `AssociateSecurityKey` and `DisassociateSecurityKey` API calls
- Track who uploaded or removed encryption keys
- Monitor for unauthorized key changes

### Network Isolation

The Lambda function performing decryption should run in a VPC with no internet access (if possible), using VPC endpoints for AWS services it needs (Secrets Manager, etc.).

---

## Limitations

- **DTMF only**: Encryption applies only to DTMF (keypad) input. Voice input cannot be encrypted through this mechanism.
- **Maximum 20 digits**: The "Store customer input" block accepts up to 20 DTMF digits.
- **One key per block**: Each "Store customer input" block uses one encryption key. Different blocks can use different keys.
- **No re-encryption in flow**: Once encrypted, the value cannot be decrypted or re-encrypted within the flow itself. Decryption must happen in Lambda.
- **Certificate format**: The public key must be an X.509 certificate in PEM format.
