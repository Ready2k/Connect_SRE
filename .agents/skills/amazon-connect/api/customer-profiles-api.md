# Amazon Connect Customer Profiles API Reference

The Customer Profiles API provides unified customer profile management with identity resolution, segmentation, and integration capabilities. It includes **80+ actions** and approximately **130+ data types**.

**SDK Package**: `@aws-sdk/client-customer-profiles`

```typescript
import { CustomerProfilesClient } from '@aws-sdk/client-customer-profiles';
const client = new CustomerProfilesClient({ region: 'us-east-1' });
```

## Actions by Category

### Domains

Domains are the top-level container for all Customer Profiles resources.

- `CreateDomain` — create a profiles domain (one per Connect instance)
- `GetDomain` — get domain details (stats, matching config)
- `UpdateDomain` — update domain settings (matching, dead letter queue)
- `DeleteDomain` — delete domain and all profiles
- `ListDomains` — list all domains in account

```typescript
import { CreateDomainCommand } from '@aws-sdk/client-customer-profiles';

const domain = await client.send(new CreateDomainCommand({
  DomainName: 'my-connect-profiles',
  DefaultExpirationDays: 365,
  DefaultEncryptionKey: 'arn:aws:kms:us-east-1:123456789012:key/xxx',
  DeadLetterQueueUrl: 'https://sqs.us-east-1.amazonaws.com/123456789012/dlq',
  Matching: {
    Enabled: true,
    AutoMerging: {
      Enabled: true,
      ConflictResolution: { ConflictResolvingModel: 'RECENCY', SourceName: 'Salesforce' },
      Consolidation: { MatchingAttributesList: [['EmailAddress'], ['PhoneNumber']] },
      MinAllowedConfidenceScoreForMerging: 0.7,
    },
  },
}));
```

### Profiles

Core profile CRUD and search operations.

- `CreateProfile` — create a customer profile
- `UpdateProfile` — update profile fields
- `DeleteProfile` — delete a profile
- `GetProfile` — get profile by ProfileId
- `SearchProfiles` — search by key-value pairs (AccountNumber, PhoneNumber, EmailAddress, etc.)
- `BatchGetProfile` — get multiple profiles by ID (up to 25)
- `MergeProfiles` — manually merge duplicate profiles
- `ListProfileObjects` — list objects linked to a profile
- `PutProfileObject` — add an object (order, case, etc.) to a profile
- `DeleteProfileObject` — remove an object
- `AddProfileKey` — add a lookup key to a profile
- `DeleteProfileKey` — remove a lookup key
- `GetProfileObjectType` — get an object type definition

```typescript
import { SearchProfilesCommand } from '@aws-sdk/client-customer-profiles';

const results = await client.send(new SearchProfilesCommand({
  DomainName: 'my-connect-profiles',
  KeyName: '_phone',
  Values: ['+15551234567'],
  MaxResults: 10,
}));

for (const profile of results.Items ?? []) {
  console.log(`${profile.FirstName} ${profile.LastName} — ${profile.ProfileId}`);
}
```

### Object Types & Templates

Object types define the schema for data objects linked to profiles.

- `CreateProfileObjectType` — define a new object type schema
- `UpdateProfileObjectType` — update object type fields/keys
- `DeleteProfileObjectType` — delete an object type
- `GetProfileObjectType` — get object type details
- `ListProfileObjectTypes` — list all object types in domain
- `GetProfileObjectTypeTemplate` — get a pre-built template (Salesforce, Marketo, etc.)
- `ListProfileObjectTypeTemplates` — list available templates

### Identity Resolution

Find and resolve duplicate profiles.

- `GetMatches` — get auto-detected duplicate profile matches
- `GetSimilarProfiles` — find profiles similar to a given profile
- `GetAutoMergingPreview` — preview what auto-merging would do
- `MergeProfiles` — merge two or more profiles into one

```typescript
import { GetMatchesCommand } from '@aws-sdk/client-customer-profiles';

const matches = await client.send(new GetMatchesCommand({
  DomainName: 'my-connect-profiles',
  MaxResults: 100,
}));

for (const match of matches.Matches ?? []) {
  console.log(`Match confidence: ${match.ConfidenceScore}`);
  console.log(`Profile IDs to merge:`, match.ProfileIds);
}
```

### Calculated Attributes

Define computed fields that aggregate across profile objects.

- `CreateCalculatedAttributeDefinition` — define a calculated attribute (SUM, COUNT, AVG, etc.)
- `UpdateCalculatedAttributeDefinition` — update definition
- `DeleteCalculatedAttributeDefinition` — delete definition
- `GetCalculatedAttributeDefinition` — get definition details
- `ListCalculatedAttributeDefinitions` — list all definitions
- `GetCalculatedAttributeForProfile` — get computed value for a specific profile
- `ListCalculatedAttributesForProfile` — list all computed values for a profile

### Segments

Define customer segments based on profile attributes and calculated attributes.

- `CreateSegmentDefinition` — create a segment with filter conditions
- `GetSegmentDefinition` — get segment definition
- `UpdateSegmentDefinition` — update segment filters
- `DeleteSegmentDefinition` — delete segment
- `ListSegmentDefinitions` — list all segments
- `CreateSegmentEstimate` — estimate segment size without materializing
- `GetSegmentEstimate` — get estimate results
- `CreateSegmentSnapshot` — materialize segment members
- `GetSegmentSnapshot` — get snapshot results
- `GetSegmentMembership` — check if profiles belong to a segment
- `BatchGetProfile` — get profiles in a segment

```typescript
import { CreateSegmentDefinitionCommand } from '@aws-sdk/client-customer-profiles';

await client.send(new CreateSegmentDefinitionCommand({
  DomainName: 'my-connect-profiles',
  SegmentDefinitionName: 'high-value-customers',
  DisplayName: 'High Value Customers',
  SegmentGroups: {
    Groups: [{
      Dimensions: [{
        CalculatedAttributes: {
          'TotalOrderValue': {
            DimensionType: 'INCLUSIVE',
            Values: [],
            ConditionOverrides: {
              Range: { Start: 10000, End: undefined, Unit: 'NONE' }
            }
          }
        }
      }],
      SourceSegments: [],
      Type: 'ALL',
    }],
    Include: 'ALL',
  },
}));
```

### Recommenders

ML-powered recommendations for profiles.

- `CreateRecommender` — create a recommender model
- `GetRecommender` — get recommender details
- `UpdateRecommender` — update configuration
- `DeleteRecommender` — delete recommender
- `ListRecommenders` — list all recommenders

### Event Triggers & Streams

React to profile changes in real-time.

- `CreateEventTrigger` — create trigger on profile events
- `GetEventTrigger` — get trigger details
- `UpdateEventTrigger` — update trigger conditions
- `DeleteEventTrigger` — delete trigger
- `ListEventTriggers` — list all triggers
- `CreateEventStream` — stream profile events to Kinesis
- `GetEventStream` — get stream details
- `DeleteEventStream` — delete stream
- `ListEventStreams` — list all streams

### Integrations (AppFlow)

Sync data from external sources.

- `PutIntegration` — create/update an AppFlow integration
- `GetIntegration` — get integration details
- `DeleteIntegration` — delete integration
- `ListIntegrations` — list all integrations
- `ListAccountIntegrations` — list integrations across domains

### Upload Jobs

Bulk import profiles from S3.

- `CreateUploadJob` — create a bulk upload job
- `GetUploadJob` — get job status
- `ListUploadJobs` — list all upload jobs

### Domain Layouts

Configure how profiles are displayed in Connect agent workspace.

- `CreateDomainLayout` — create layout
- `GetDomainLayout` — get layout
- `UpdateDomainLayout` — update layout
- `DeleteDomainLayout` — delete layout
- `ListDomainLayouts` — list layouts

## Key Data Types

### Profile

```typescript
interface Profile {
  ProfileId: string;
  AccountNumber?: string;
  AdditionalInformation?: string;
  PartyType?: 'INDIVIDUAL' | 'BUSINESS' | 'OTHER';
  BusinessName?: string;
  FirstName?: string;
  MiddleName?: string;
  LastName?: string;
  BirthDate?: string;
  Gender?: 'MALE' | 'FEMALE' | 'UNSPECIFIED';
  PhoneNumber?: string;
  MobilePhoneNumber?: string;
  HomePhoneNumber?: string;
  BusinessPhoneNumber?: string;
  EmailAddress?: string;
  PersonalEmailAddress?: string;
  BusinessEmailAddress?: string;
  Address?: Address;
  ShippingAddress?: Address;
  MailingAddress?: Address;
  BillingAddress?: Address;
  Attributes?: Record<string, string>;
  FoundByItems?: FoundByKeyValue[];
  PartyTypeString?: string;
  GenderString?: string;
}
```

### Address

```typescript
interface Address {
  Address1?: string;
  Address2?: string;
  Address3?: string;
  Address4?: string;
  City?: string;
  County?: string;
  State?: string;
  Province?: string;
  Country?: string;
  PostalCode?: string;
}
```

### MatchItem

```typescript
interface MatchItem {
  MatchId: string;
  ProfileIds: string[];
  ConfidenceScore: number;
}
```

### SegmentDefinitionItem

```typescript
interface SegmentDefinitionItem {
  SegmentDefinitionName: string;
  DisplayName: string;
  SegmentDefinitionArn: string;
  Description?: string;
  CreatedAt: Date;
  Tags?: Record<string, string>;
}
```
