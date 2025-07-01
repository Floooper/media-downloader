import { faker } from '@faker-js/faker';

interface User {
  id: string;
  username: string;
  email: string;
  name: string;
  avatar: string;
  createdAt: Date;
  updatedAt: Date;
  role: string;
  settings: UserSettings;
}

interface UserSettings {
  theme: string;
  language: string;
  notifications: {
    email: boolean;
    push: boolean;
    desktop: boolean;
  };
  downloadPath: string;
}

interface Tag {
  id: string;
  name: string;
  color: string;
  description: string;
  createdAt: Date;
  updatedAt: Date;
}

interface MediaServer {
  id: string;
  name: string;
  type: string;
  url: string;
  apiKey: string;
  status: string;
  createdAt: Date;
  updatedAt: Date;
}

interface Download {
  id: string;
  url: string;
  title: string;
  description: string;
  status: string;
  progress: number;
  size: number;
  downloadedSize: number;
  createdAt: Date;
  updatedAt: Date;
  userId: string;
  mediaServerId: string;
  tags: Tag[];
  metadata: DownloadMetadata;
}

interface DownloadMetadata {
  title: string;
  year: number;
  type: string;
  genres: string[];
  rating: number;
  duration: number;
  language: string;
}

interface MediaFile {
  id: string;
  filename: string;
  mimeType: string;
  size: number;
  path: string;
  metadata: {
    width: number;
    height: number;
    duration: number;
    bitrate: number;
    codec: string;
    audioCodec: string;
    fps: number;
    aspectRatio: string;
  };
  thumbnailUrl: string;
  createdAt: Date;
  updatedAt: Date;
  downloadId: string;
}

interface Notification {
  id: string;
  type: string;
  title: string;
  message: string;
  read: boolean;
  createdAt: Date;
  userId: string;
}

type GenerateOptions<T> = {
  count?: number;
  seed?: number;
  overrides?: Partial<T>;
};

class TestDataGenerator {
  private seed: number;

  constructor(seed = 123) {
    this.seed = seed;
    this.setSeed(seed);
  }

  setSeed(seed: number): void {
    this.seed = seed;
    faker.seed(seed);
  }

  reset(): void {
    this.setSeed(this.seed);
  }

  user(overrides: Partial<User> = {}): User {
    return {
      id: faker.string.uuid(),
      username: faker.internet.userName(),
      email: faker.internet.email(),
      name: faker.person.fullName(),
      avatar: faker.image.avatar(),
      createdAt: faker.date.past(),
      updatedAt: faker.date.recent(),
      role: faker.helpers.arrayElement(['admin', 'user']),
      settings: this.userSettings(),
      ...overrides,
    };
  }

  userSettings(overrides: Partial<UserSettings> = {}): UserSettings {
    return {
      theme: faker.helpers.arrayElement(['light', 'dark', 'system']),
      language: faker.helpers.arrayElement(['en', 'es', 'fr', 'de']),
      notifications: {
        email: faker.datatype.boolean(),
        push: faker.datatype.boolean(),
        desktop: faker.datatype.boolean(),
      },
      downloadPath: faker.system.directoryPath(),
      ...overrides,
    };
  }

  tag(overrides: Partial<Tag> = {}): Tag {
    return {
      id: faker.string.uuid(),
      name: faker.lorem.word(),
      color: faker.internet.color(),
      description: faker.lorem.sentence(),
      createdAt: faker.date.past(),
      updatedAt: faker.date.recent(),
      ...overrides,
    };
  }

  mediaServer(overrides: Partial<MediaServer> = {}): MediaServer {
    return {
      id: faker.string.uuid(),
      name: faker.lorem.word(),
      type: faker.helpers.arrayElement(['plex', 'emby', 'jellyfin']),
      url: faker.internet.url(),
      apiKey: faker.string.alphanumeric(32),
      status: faker.helpers.arrayElement(['online', 'offline', 'error']),
      createdAt: faker.date.past(),
      updatedAt: faker.date.recent(),
      ...overrides,
    };
  }

  download(overrides: Partial<Download> = {}): Download {
    return {
      id: faker.string.uuid(),
      url: faker.internet.url(),
      title: faker.lorem.sentence(),
      description: faker.lorem.paragraph(),
      status: faker.helpers.arrayElement([
        'pending',
        'downloading',
        'processing',
        'completed',
        'failed',
        'cancelled',
      ]),
      progress: faker.number.float({ min: 0, max: 100, precision: 0.1 }),
      size: faker.number.int({ min: 1000000, max: 1000000000 }),
      downloadedSize: faker.number.int({ min: 0, max: 1000000000 }),
      createdAt: faker.date.past(),
      updatedAt: faker.date.recent(),
      userId: faker.string.uuid(),
      mediaServerId: faker.string.uuid(),
      tags: Array.from({ length: faker.number.int({ min: 0, max: 3 }) }, () =>
        this.tag()
      ),
      metadata: this.downloadMetadata(),
      ...overrides,
    };
  }

  downloadMetadata(overrides: Partial<DownloadMetadata> = {}): DownloadMetadata {
    return {
      title: faker.lorem.sentence(),
      year: faker.number.int({ min: 1900, max: 2024 }),
      type: faker.helpers.arrayElement(['movie', 'series', 'music']),
      genres: Array.from(
        { length: faker.number.int({ min: 1, max: 4 }) },
        () => faker.word.noun()
      ),
      rating: faker.number.float({ min: 0, max: 10, precision: 0.1 }),
      duration: faker.number.int({ min: 300, max: 18000 }), // in seconds
      language: faker.helpers.arrayElement(['en', 'es', 'fr', 'de']),
      ...overrides,
    };
  }

  mediaFile(overrides: Partial<MediaFile> = {}): MediaFile {
    return {
      id: faker.string.uuid(),
      filename: faker.system.fileName(),
      mimeType: faker.system.mimeType(),
      size: faker.number.int({ min: 1000000, max: 1000000000 }),
      path: faker.system.filePath(),
      metadata: {
        width: faker.number.int({ min: 800, max: 3840 }),
        height: faker.number.int({ min: 600, max: 2160 }),
        duration: faker.number.float({ min: 30, max: 7200 }),
        bitrate: faker.number.int({ min: 1000000, max: 10000000 }),
        codec: faker.helpers.arrayElement(['h264', 'h265', 'vp9']),
        audioCodec: faker.helpers.arrayElement(['aac', 'mp3', 'ac3']),
        fps: faker.number.int({ min: 24, max: 60 }),
        aspectRatio: faker.helpers.arrayElement(['16:9', '21:9', '4:3']),
      },
      thumbnailUrl: faker.image.url(),
      createdAt: faker.date.past(),
      updatedAt: faker.date.recent(),
      downloadId: faker.string.uuid(),
      ...overrides,
    };
  }

  notification(overrides: Partial<Notification> = {}): Notification {
    return {
      id: faker.string.uuid(),
      type: faker.helpers.arrayElement(['info', 'success', 'warning', 'error']),
      title: faker.lorem.sentence(),
      message: faker.lorem.paragraph(),
      read: faker.datatype.boolean(),
      createdAt: faker.date.past(),
      userId: faker.string.uuid(),
      ...overrides,
    };
  }

  // Generic list generator
  generate<T>(
    generator: (overrides?: Partial<T>) => T,
    { count = 1, seed, overrides }: GenerateOptions<T> = {}
  ): T[] {
    if (seed) this.setSeed(seed);
    return Array.from({ length: count }, () => generator(overrides));
  }

  // Convenience methods for generating lists
  users(options: GenerateOptions<User> = {}) {
    return this.generate(this.user.bind(this), options);
  }

  tags(options: GenerateOptions<Tag> = {}) {
    return this.generate(this.tag.bind(this), options);
  }

  mediaServers(options: GenerateOptions<MediaServer> = {}) {
    return this.generate(this.mediaServer.bind(this), options);
  }

  downloads(options: GenerateOptions<Download> = {}) {
    return this.generate(this.download.bind(this), options);
  }

  mediaFiles(options: GenerateOptions<MediaFile> = {}) {
    return this.generate(this.mediaFile.bind(this), options);
  }

  notifications(options: GenerateOptions<Notification> = {}) {
    return this.generate(this.notification.bind(this), options);
  }
}

export const testData = new TestDataGenerator();
