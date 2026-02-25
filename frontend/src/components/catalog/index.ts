// A2UI Primitive Component Catalog Registry
import { Text } from './Text';
import { Image } from './Image';
import { Button } from './Button';
import { Row } from './Row';
import { Column } from './Column';
import { Card } from './Card';
import { List } from './List';
import { Divider } from './Divider';
import { Progress } from './Progress';
import { Chip } from './Chip';
import { StepCarousel } from './StepCarousel';

export const componentCatalog: Record<string, React.ComponentType<any>> = {
  Text,
  Image,
  Button,
  Row,
  Column,
  Card,
  List,
  Divider,
  Progress,
  Chip,
  StepCarousel,
};

export { Text, Image, Button, Row, Column, Card, List, Divider, Progress, Chip, StepCarousel };

